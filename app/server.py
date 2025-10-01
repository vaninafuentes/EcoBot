# app/server.py
from rich.console import Console
from app.config import BOT_NAME, BOT_VERSION
from app.router import route_question
import os, redis
from datetime import datetime

console = Console()

# --- Conexión obligatoria al Redis del contenedor ---
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")  # <-- SIEMPRE 'redis'
try:
    r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    r.ping()
except Exception as e:
    raise SystemExit(f"⚠️ No pude conectar a Redis en {REDIS_URL}: {e}")

def _meta_key(session_id: str) -> str:
    return f"session:{session_id}:meta"

def _hist_key(session_id: str) -> str:
    return f"session:{session_id}:history"

def _init_session(session_id: str):
    """Crea la sesión en Redis apenas ingresás el nombre."""
    meta = _meta_key(session_id)
    hist = _hist_key(session_id)

    now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    created = r.hget(meta, "created_at") or now
    r.hset(meta, mapping={
        "user": session_id,
        "created_at": created,
        "last_active": now,
        "source": "cli",
        "messages": r.llen(hist) or 0,
    })
    # Si no hay mensaje de bienvenida aún, lo ponemos
    if r.llen(hist) == 0:
        r.rpush(hist, "EcoBot: ¡Hola! Empecemos cuando quieras. 😊")
        r.hset(meta, "messages", r.llen(hist))

    return meta, hist

def _load_history_for_llm(hist_key: str):
    """Convierte 'Tú: ...' / 'EcoBot: ...' en [{role, content}] para route_question."""
    msgs = r.lrange(hist_key, 0, -1)
    parsed = []
    for raw in msgs:
        if raw.startswith("Tú: "):
            parsed.append({"role": "user", "content": raw[4:]})
        elif raw.startswith("EcoBot: "):
            parsed.append({"role": "assistant", "content": raw[8:]})
        else:
            # fallback: lo tratamos como assistant
            parsed.append({"role": "assistant", "content": raw})
    return parsed

def _append_turn(meta_key: str, hist_key: str, question: str, answer: str):
    r.rpush(hist_key, f"Tú: {question}")
    r.rpush(hist_key, f"EcoBot: {answer}")
    now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    r.hset(meta_key, mapping={"last_active": now, "messages": r.llen(hist_key)})

def main():
    console.print(f"[bold green]{BOT_NAME} v{BOT_VERSION}[/bold green]")
    console.print("Charla abierta (económica por defecto). Escribí 'salir' para terminar.\n")

    session_id = console.input("[yellow]Elegí tu nombre de usuario:[/yellow] ").strip() or "cli-default"
    meta_key, hist_key = _init_session(session_id)
    console.print(f"[cyan]Sesión iniciada como:[/cyan] {session_id}\n")

    while True:
        question = console.input("[bold blue]Tú[/bold blue]: ")
        if question.strip().lower() in {"salir", "exit", "quit"}:
            console.print("[red]Cerrando EcoBot...[/red]")
            break

        history_for_llm = _load_history_for_llm(hist_key)
        answer = route_question(question, history=history_for_llm)

        _append_turn(meta_key, hist_key, question, answer)
        console.print(f"[bold green]{BOT_NAME}[/bold green]: {answer}\n")

if __name__ == "__main__":
    main()
