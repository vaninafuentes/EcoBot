# app/server_api.py
import os, json, uuid
from typing import Optional, List, Dict, Any

from fastapi import Body, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime
from zoneinfo import ZoneInfo

import redis
from dotenv import load_dotenv, find_dotenv

from app.router import route_question  # tu router de siempre

# =========================
# Config & entorno
# =========================
load_dotenv(find_dotenv(), override=True)

APP_NAME = "EcoBot API"
API_KEY = os.getenv("ECOBOT_API_KEY")  # opcional
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
SESSION_TTL = int(os.getenv("SESSION_TTL", "86400"))  # 24h por defecto
TZ = ZoneInfo("America/Argentina/Mendoza")

# =========================
# Redis (o fallback en memoria)
# =========================
r: Optional[redis.Redis]
try:
    r = redis.from_url(REDIS_URL, decode_responses=True)
    r.ping()
except Exception:
    r = None
    _MEM_STORE: Dict[str, Any] = {}

def _session_key(session_id: str) -> str:
    return f"ecobot:session:{session_id}"

def _meta_key(session_id: str) -> str:
    return f"ecobot:session_meta:{session_id}"

def get_history(session_id: str) -> List[Dict[str, Any]]:
    if not session_id:
        return []
    if r:
        raw = r.get(_session_key(session_id))
        if not raw:
            return []
        try:
            return json.loads(raw)
        except Exception:
            return []
    else:
        return _MEM_STORE.get(_session_key(session_id), [])

def set_history(session_id: str, history: List[Dict[str, Any]], ttl_seconds: int = SESSION_TTL) -> None:
    if not session_id:
        return
    if r:
        # guardamos historial y aplicamos TTL para autolimpieza
        r.set(_session_key(session_id), json.dumps(history), ex=ttl_seconds)
    else:
        _MEM_STORE[_session_key(session_id)] = history

# =========================
# FastAPI app & modelos
# =========================
app = FastAPI(title=APP_NAME)

class AskRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class AskResponse(BaseModel):
    session_id: str
    reply: str

class NewSessionIn(BaseModel):
    name: Optional[str] = None

# =========================
# Endpoints
# =========================
@app.get("/healthz")
def healthz():
    return {"ok": True, "redis": bool(r)}

@app.post("/new_session")
def new_session(payload: NewSessionIn):
    """
    Crea una sesión nueva. Guarda metadatos en Redis:
      - name: nombre amigable de la sesión
      - started_at: ISO con tz de Mendoza
      - last_seen: actualizado en cada /ask
    """
    sid = str(uuid.uuid4())
    started_at = datetime.now(TZ).isoformat(timespec="seconds")
    session_name = (payload.name or "").strip() or f"sesion-{sid[:8]}"

    if r:
        # Guardamos meta como HASH y aplicamos TTL también
        r.hset(_meta_key(sid), mapping={
            "name": session_name,
            "started_at": started_at,
            "last_seen": started_at
        })
        r.expire(_meta_key(sid), SESSION_TTL)
    else:
        _MEM_STORE[f"{sid}:name"] = session_name
        _MEM_STORE[f"{sid}:started_at"] = started_at
        _MEM_STORE[f"{sid}:last_seen"] = started_at

    return {"session_id": sid, "name": session_name, "started_at": started_at}

@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest, x_api_key: Optional[str] = Header(default=None)):
    if API_KEY:
        print(API_KEY)
        if not x_api_key or x_api_key != API_KEY:
            raise HTTPException(status_code=401, detail="API key inválida")

    # Si no viene session_id, creamos uno (aunque lo normal es que venga del CLI)
    session_id = req.session_id or str(uuid.uuid4())
    history = get_history(session_id)

    # Guardar mensaje del usuario
    history.append({"role": "user", "content": req.message})
    set_history(session_id, history)

    # Generar respuesta con tu router/LLM
    reply = route_question(req.message, history=history)

    # Guardar respuesta del asistente
    history.append({"role": "assistant", "content": reply})
    set_history(session_id, history)

    # Actualizar last_seen en meta + renovar TTL
    now_s = datetime.now(TZ).isoformat(timespec="seconds")
    if r:
        r.hset(_meta_key(session_id), mapping={"last_seen": now_s})
        r.expire(_meta_key(session_id), SESSION_TTL)
    else:
        _MEM_STORE[f"{session_id}:last_seen"] = now_s

    return AskResponse(session_id=session_id, reply=reply)

@app.delete("/reset/{session_id}")
def reset_session(session_id: str):
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id requerido")
    if r:
        r.delete(_session_key(session_id))
        r.delete(_meta_key(session_id))
    else:
        try: del _MEM_STORE[_session_key(session_id)]
        except Exception: pass
        for suffix in (":name", ":started_at", ":last_seen"):
            try: del _MEM_STORE[f"{session_id}{suffix}"]
            except Exception: pass
    return {"ok": True}

@app.get("/sessions")
def list_sessions(limit: int = Query(100, ge=1, le=1000)):
    """
    Lista sesiones (name, session_id, started_at, last_seen) leyendo solo los metadatos.
    Ordena por started_at desc.
    """
    items: List[Dict[str, Any]] = []
    if r:
        cursor = 0
        count = 0
        pattern = "ecobot:session_meta:*"
        while True:
            cursor, keys = r.scan(cursor=cursor, match=pattern, count=1000)
            for k in keys:
                sid = k.split("ecobot:session_meta:")[-1]
                meta = r.hgetall(k) or {}
                items.append({
                    "session_id": sid,
                    "name": meta.get("name"),
                    "started_at": meta.get("started_at"),
                    "last_seen": meta.get("last_seen"),
                })
                count += 1
                if count >= limit:
                    break
            if cursor == 0 or count >= limit:
                break
    else:
        # Fallback en memoria
        acc: Dict[str, Dict[str, Any]] = {}
        for k, v in _MEM_STORE.items():
            if k.endswith(":name") or k.endswith(":started_at") or k.endswith(":last_seen"):
                sid, suffix = k.rsplit(":", 1)
                acc.setdefault(sid, {})
                acc[sid][suffix] = v
        for sid, meta in acc.items():
            items.append({
                "session_id": sid,
                "name": meta.get("name"),
                "started_at": meta.get("started_at"),
                "last_seen": meta.get("last_seen"),
            })
        items = items[:limit]

    items.sort(key=lambda x: (x.get("started_at") or ""), reverse=True)
    return {"sessions": items}
