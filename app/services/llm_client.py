# app/services/llm_client.py
"""
Capa de integración con el proveedor de LLM (Groq).

Este módulo expone la función principal:

    chat_teacher(messages, temperature=0.55, max_tokens=380) -> str

que:
  - Toma una lista de mensajes estilo Chat (dicts con "role" y "content").
  - Llama al modelo configurado en Groq.
  - Devuelve el contenido de texto de la respuesta.

Si la configuración es incorrecta (por ejemplo, falta GROQ_API_KEY),
lanza RuntimeError para que la capa superior (router) decida qué mostrar
al usuario.
"""

from __future__ import annotations

import os
from typing import List, Dict, Any

from dotenv import load_dotenv, find_dotenv

# Cargamos variables de entorno desde .env (si existe)
load_dotenv(find_dotenv(), override=True)
load_dotenv()

# -----------------------------
# Configuración del proveedor
# -----------------------------

LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq").lower()
GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY")
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

_groq_client = None

if LLM_PROVIDER == "groq" and GROQ_API_KEY:
    try:
        from groq import Groq  # type: ignore
        _groq_client = Groq(api_key=GROQ_API_KEY)
    except Exception:
        # Si falla la importación o inicialización, dejamos el cliente en None.
        # El error se comunicará al intentar usarlo.
        _groq_client = None


# -----------------------------
# Implementación Groq
# -----------------------------

def _chat_groq(
    messages: List[Dict[str, Any]],
    temperature: float = 0.55,
    max_tokens: int = 380,
) -> str:
    """
    Envía una conversación al modelo de Groq y devuelve el texto de la respuesta.

    Lanza RuntimeError si el cliente no está inicializado o si ocurre
    algún error al consultar la API de Groq.
    """
    if _groq_client is None:
        raise RuntimeError(
            "Cliente de Groq no inicializado. "
            "Verificá que LLM_PROVIDER='groq' y que GROQ_API_KEY esté configurada."
        )

    try:
        response = _groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except Exception as exc:
        # Propagamos un error claro hacia arriba; el router decide qué mostrar al usuario.
        raise RuntimeError(f"Error al consultar el modelo de Groq: {exc}") from exc

    # Asumimos que hay al menos una choice con contenido
    choice = response.choices[0]
    content = getattr(choice.message, "content", "") or ""
    return content.strip()


# -----------------------------
# Fachada pública
# -----------------------------

def chat_teacher(
    messages: List[Dict[str, Any]],
    temperature: float = 0.55,
    max_tokens: int = 380,
) -> str:
    """
    Punto de entrada único para el resto de la aplicación.

    Actualmente solo soporta Groq como proveedor. Si en el futuro se
    quisiera agregar otro proveedor, se podría extender aquí mismo
    con un 'if LLM_PROVIDER == "...": ...'.

    Parámetros:
      - messages: lista de mensajes estilo chat [{"role": "system"|"user"|"assistant", "content": "..."}]
      - temperature: controla la variabilidad de las respuestas.
      - max_tokens: límite de tokens que puede generar la respuesta.

    Devuelve:
      - Texto de la respuesta del modelo (string).
    """
    if LLM_PROVIDER != "groq":
        raise RuntimeError(
            f"LLM_PROVIDER='{LLM_PROVIDER}' no soportado. "
            "Actualmente la aplicación está preparada solo para 'groq'."
        )

    return _chat_groq(messages, temperature=temperature, max_tokens=max_tokens)
