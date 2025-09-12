# app/router.py
from app.services.econ_resources import answer_from_kb
from app.services.didactica import build_messages
from app.services.llm_client import chat_teacher

def route_question(question: str, history=None) -> str:
    """
    Router único:
    1) Si la KB tiene respuesta, devuelve una versión didáctica corta (sin usar la API).
    2) Si no, usa el LLM con memoria corta de charla para mantener fluidez.
    """
    kb = answer_from_kb(question)
    if kb:
        return (
            "• Definición: " + kb +
            "\n• Intuición: Es la idea central del concepto."
            "\n• Mini-check: ¿Querés que lo veamos con un numerito rápido?"
        )

    msgs = build_messages(question, history=history)
    return chat_teacher(msgs, temperature=0.55, max_tokens=380)
