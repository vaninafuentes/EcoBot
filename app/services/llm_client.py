import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(), override=True)

load_dotenv()

# Configuración de proveedor y claves
PROVIDER = os.getenv("LLM_PROVIDER").lower()  # 'groq'
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Modelos por defecto
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


# --- Groq ---
_groq_client = None
if PROVIDER == "groq" and GROQ_API_KEY:
    from groq import Groq
    _groq_client = Groq(api_key=GROQ_API_KEY)

def _chat_groq(messages, temperature=0.55, max_tokens=380) -> str:
    if not _groq_client:
        return "⚠️ Falta GROQ_API_KEY o provider mal configurado."
    try:
        resp = _groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Error en Groq: {e}"

# --- Facade ---
def chat_teacher(messages, temperature=0.55, max_tokens=380) -> str:
    if PROVIDER == "groq":
        return _chat_groq(messages, temperature, max_tokens)
    # default: OpenAI
    return _chat_openai(messages, temperature, max_tokens)
