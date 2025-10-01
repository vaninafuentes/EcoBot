import os, json, uuid
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Header
from pydantic import BaseModel
import redis
from dotenv import load_dotenv, find_dotenv

from app.router import route_question  # usa tu router “como antes”

# Cargar .env
load_dotenv(find_dotenv(), override=True)

APP_NAME = "EcoBot API"
API_KEY = os.getenv("ECOBOT_API_KEY")  # opcional
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Redis o fallback en memoria
r: Optional[redis.Redis]
try:
    r = redis.from_url(REDIS_URL, decode_responses=True)
    r.ping()
except Exception:
    r = None
    _MEM_STORE: Dict[str, List[Dict[str, Any]]] = {}

def _session_key(session_id: str) -> str:
    return f"ecobot:session:{session_id}"

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
        return _MEM_STORE.get(session_id, [])

def set_history(session_id: str, history: List[Dict[str, Any]]) -> None:
    if not session_id:
        return
    if r:
        r.set(_session_key(session_id), json.dumps(history))
    else:
        _MEM_STORE[session_id] = history

app = FastAPI(title=APP_NAME)

class AskRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class AskResponse(BaseModel):
    session_id: str
    reply: str

@app.get("/healthz")
def healthz():
    return {"ok": True, "redis": bool(r)}

@app.post("/new_session")
def new_session():
    return {"session_id": uuid.uuid4().rfc4122}

@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest, x_api_key: Optional[str] = Header(default=None)):
    if API_KEY:
        if not x_api_key or x_api_key != API_KEY:
            raise HTTPException(status_code=401, detail="API key inválida")

    session_id = req.session_id or uuid.uuid4().rfc4122
    history = get_history(session_id)

    history.append({"role": "user", "content": req.message})
    set_history(session_id, history)

    reply = route_question(req.message, history=history)

    history.append({"role": "assistant", "content": reply})
    set_history(session_id, history)

    return AskResponse(session_id=session_id, reply=reply)

@app.delete("/reset/{session_id}")
def reset_session(session_id: str):
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id requerido")
    if r:
        r.delete(_session_key(session_id))
    else:
        try: del _MEM_STORE[session_id]
        except Exception: pass
    return {"ok": True}
