from typing import List, Dict
from collections import deque
from app.prompts.promptedu import EDU_PROMPT

# Mantener últimas N interacciones (en server lo creamos y se lo pasamos)
def build_messages(question: str, history: List[Dict[str, str]] | None = None) -> List[Dict[str, str]]:
    msgs: List[Dict[str, str]] = [{"role": "system", "content": EDU_PROMPT}]
    # adjuntar historial reciente (mantenerlo corto para no gastar tokens)
    if history:
        # Tomamos como mucho las últimas 6 entradas
        short = list(deque(history, maxlen=6))
        msgs.extend(short)
    # la pregunta actual
    msgs.append({"role": "user", "content": question})
    return msgs
