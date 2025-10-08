import os, json, requests

API_URL = os.getenv("ECOBOT_URL", "http://localhost:8000")
API_KEY = os.getenv("ECOBOT_API_KEY", "demo-secret")

def new_session(name: str):
    headers = {"X-API-KEY": API_KEY, "Content-Type": "application/json"}
    body = {"name": name}
    r = requests.post(f"{API_URL}/new_session", headers=headers, data=json.dumps(body))
    r.raise_for_status()
    d = r.json()
    return d["session_id"], d.get("name"), d.get("started_at")

def ask(session_id: str, text: str) -> str:
    headers = {"X-API-KEY": API_KEY, "Content-Type": "application/json"}
    body = {"message": text, "session_id": session_id}
    r = requests.post(f"{API_URL}/ask", headers=headers, data=json.dumps(body))
    r.raise_for_status()
    return r.json()["reply"]

def main():
    name = input("👤 Escribí un nombre para tu sesión: ").strip() or "anonimo"
    session_id, name_srv, started = new_session(name)
    print(f"🆕 Sesión '{name_srv}' iniciada (ID: {session_id[:8]}) [{started}]")

    while True:
        try:
            msg = input("> ").strip()
            if not msg:
                continue
            if msg.lower() in {"!salir", "salir"}:
                print("👋 Chau!")
                break
            print(f"🤖 {ask(session_id, msg)}\n")
        except KeyboardInterrupt:
            print("\n👋 Chau!")
            break
        except Exception as e:
            print(f"⚠️ Error: {e}")

if __name__ == "__main__":
    main()
