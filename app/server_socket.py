# app/server_socket.py
"""
Servidor de sockets de EcoBot.

Objetivo:
  - Cada conexión TCP representa una sesión independiente.
  - Cada sesión tiene su propio session_id interno.
  - El historial de la conversación se guarda en memoria, por session_id.
  - El admin puede listar sesiones activas y matar una conexión (kill).

No usa Redis ni FastAPI: las sesiones viven en memoria del proceso
"""

from __future__ import annotations

import os
import socket
import threading
import json
from datetime import datetime, timezone
import uuid
import itertools
from typing import Dict, List, Any, Tuple

from app.router import route_question  # router económico de siempre


# ---------------------------
# Configuración básica
# ---------------------------

HOST: str = "0.0.0.0"
PORT: int = int(os.getenv("ECOBOT_SOCKET_PORT", "5001"))

# Historial de cada sesión en memoria:
#   session_id -> [ { "role": "user"/"assistant", "content": str }, ... ]
SESSION_HISTORIES: Dict[str, List[Dict[str, str]]] = {}

# Conexiones activas (para admin list / kill):
#   session_id -> {
#       "addr", "thread", "started_at", "last_seen",
#       "conn", "number"
#   }
active_connections: Dict[str, Dict[str, Any]] = {}
active_lock = threading.Lock()  # protege active_connections y SESSION_HISTORIES

# Contador incremental para etiquetar las sesiones como
# "Sesión 1", "Sesión 2", etc.
SESSION_SEQ = itertools.count(1)

# Opcional: límite de turnos por sesión (para que el historial no crezca infinito)
MAX_TURNS_PER_SESSION = 40  # 20 preguntas + 20 respuestas


# ---------------------------
# Helpers generales
# ---------------------------

def _make_session_id() -> str:
    """
    Genera un ID de sesión corto y amigable, tipo 'e750230a'.
    (similar al conversation_id de PsicoIA).
    """
    return uuid.uuid4().hex[:8]


def _now_iso() -> str:
    """Devuelve fecha-hora actual en ISO con zona local."""
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def get_session_history(session_id: str) -> List[Dict[str, str]]:
    """
    Obtiene el historial de una sesión específica.
    Si no existe, devuelve lista vacía.
    """
    with active_lock:
        return list(SESSION_HISTORIES.get(session_id, []))


def append_turn(session_id: str, user_msg: str, bot_msg: str) -> None:
    """
    Agrega al historial de la sesión:
      - el mensaje del usuario
      - la respuesta del bot
    y trunca si supera MAX_TURNS_PER_SESSION.
    """
    if not session_id:
        return

    with active_lock:
        history = SESSION_HISTORIES.get(session_id)
        if history is None:
            history = []
            SESSION_HISTORIES[session_id] = history

        history.append({"role": "user", "content": user_msg})
        history.append({"role": "assistant", "content": bot_msg})

        # Truncar historial si se excede el máximo
        max_len = 2 * MAX_TURNS_PER_SESSION
        if len(history) > max_len:
            del history[:-max_len]


# ---------------------------
# Lógica por cliente (un hilo por conexión)
# ---------------------------

def handle_client(conn: socket.socket, addr: Tuple[str, int]) -> None:
    """
    Maneja una conexión TCP completa:
      - crea un session_id
      - asigna un número de sesión (1, 2, 3, ...)
      - recibe mensajes del usuario
      - llama al router con el historial de ESA sesión
      - guarda historial en memoria
      - responde al cliente
    """
    session_id = _make_session_id()
    session_number = next(SESSION_SEQ)  # Sesión 1, 2, 3...

    # Registramos la conexión en el mapa de conexiones activas
    with active_lock:
        active_connections[session_id] = {
            "addr": addr,
            "thread": threading.current_thread().name,
            "started_at": _now_iso(),
            "last_seen": _now_iso(),
            "conn": conn,
            "number": session_number,
        }

    print(f"[Sesión {session_number}] Nueva conexión desde {addr} (sid={session_id})")

    try:
        welcome = (
            "Bienvenido a EcoBot👋\n"
            f"Tu session_id es: {session_id}\n"
            "Escribí tu pregunta de economía o 'salir' para desconectarte.\n\n> "
        )
        conn.sendall(welcome.encode("utf-8"))

        while True:
            data = conn.recv(4096)
            if not data:
                # el cliente cerró la conexión
                break

            message = data.decode("utf-8", errors="ignore").strip()
            if not message:
                conn.sendall(b"> ")
                continue

            # Comandos de salida
            if message.lower() in {"salir", "exit", "quit"}:
                goodbye = "👋 Cerrando sesión. Gracias por usar EcoBot.\n"
                conn.sendall(goodbye.encode("utf-8"))
                break

            # Historia actual de ESA sesión (no se mezcla con otras)
            history = get_session_history(session_id)

            # Llamamos al router (KB + plots + LLM)
            try:
                answer_text = route_question(message, history=history)
            except Exception as exc:
                answer_text = f"Ocurrió un error interno en el bot: {exc}"

            # Guardamos turno en el historial en memoria
            append_turn(session_id, message, answer_text)

            # Actualizamos el last_seen de esta conexión
            with active_lock:
                if session_id in active_connections:
                    active_connections[session_id]["last_seen"] = _now_iso()

            # Enviamos respuesta y dejamos listo el prompt
            response = f"\nEcoBot: {answer_text}\n\n> "
            conn.sendall(response.encode("utf-8"))

    except Exception as exc:
        # Intentamos avisar al cliente si hay error
        try:
            conn.sendall(f"\n[ERROR] {exc}\n".encode("utf-8"))
        except Exception:
            pass
    finally:
        # Limpieza al cerrar la conexión
        with active_lock:
            info = active_connections.pop(session_id, None)
        try:
            conn.close()
        except Exception:
            pass

        num = info.get("number") if info else "?"
        print(f"[Sesión {num}] Conexión cerrada {addr} (sid={session_id})")


# ---------------------------
# Consola admin: list / kill
# ---------------------------

def admin_console() -> None:
    """
    Consola interactiva para el admin.

    Comandos:
      - list            -> muestra sesiones activas
      - kill <sid>      -> cierra la conexión de esa sesión (por session_id)
      - exit / quit     -> cierra la consola admin (el servidor sigue corriendo)
    """
    print("Consola admin lista. Comandos: list, kill <session_id>, exit")

    while True:
        try:
            cmd = input("(admin)> ").strip()
        except EOFError:
            break

        if not cmd:
            continue

        if cmd == "list":
            with active_lock:
                if not active_connections:
                    print("No hay conexiones activas.")
                else:
                    for sid, info in active_connections.items():
                        num = info.get("number", "?")
                        print(
                            f"Sesión {num} ({sid}) | {info['addr']} | "
                            f"hilo={info['thread']} | "
                            f"started={info['started_at']} | "
                            f"last_seen={info['last_seen']}"
                        )

        elif cmd.startswith("kill "):
            parts = cmd.split(maxsplit=1)
            if len(parts) != 2:
                print("Uso: kill <session_id>")
                continue

            sid = parts[1].strip()

            with active_lock:
                info = active_connections.get(sid)
                if not info:
                    print("No existe esa sesión o ya está cerrada.")
                    continue

                conn = info.get("conn")
                try:
                    conn.shutdown(socket.SHUT_RDWR)
                    conn.close()
                except Exception:
                    pass

                active_connections.pop(sid, None)

            print(f"Sesión {sid} cerrada desde admin.")

        elif cmd in {"exit", "quit"}:
            print("Saliendo consola admin (el server sigue corriendo)...")
            break

        else:
            print("Comandos disponibles: list, kill <session_id>, exit")


# ---------------------------
# Main server socket
# ---------------------------

def start_server() -> None:
    """
    Inicia el servidor de sockets de EcoBot.

    - Escucha en HOST:PORT.
    - Por cada conexión entrante, crea un hilo que ejecuta handle_client.
    - Lanza la consola admin en un hilo separado.
    """
    print(f"EcoBot socket server escuchando en {HOST}:{PORT} ...")

    # Lanzar consola admin en otro hilo (para poder usar list/kill)
    threading.Thread(target=admin_console, daemon=True).start()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, PORT))
        server_socket.listen()

        try:
            while True:
                conn, addr = server_socket.accept()
                thread = threading.Thread(
                    target=handle_client,
                    args=(conn, addr),
                    daemon=True,
                    name="handle_client",
                )
                thread.start()
        except KeyboardInterrupt:
            print("\n⏹ Apagando servidor EcoBot socket...")


if __name__ == "__main__":
    start_server()
