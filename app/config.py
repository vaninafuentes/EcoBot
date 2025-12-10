# app/config.py
"""
Constantes globales de EcoBot.
Se importan desde otros módulos para evitar 'números mágicos'
y strings repetidos.
"""

# Identidad del bot
BOT_NAME = "EcoBot"
BOT_VERSION = "1.0"

# Carpeta para guardar gráficos
OUT_DIR_NAME = "out"

# LLM (Groq)
DEFAULT_LLM_MODEL = "llama-3.3-70b-versatile"
DEFAULT_TEMPERATURE = 0.55
DEFAULT_MAX_TOKENS = 380

# Sesiones / contexto
MAX_HISTORY_ENTRIES = 6   # mensajes de historial que se pasan al LLM
SESSION_ID_LENGTH = 8     # ej: 'e750230a'

# Servidores (opcional)
DEFAULT_SOCKET_HOST = "0.0.0.0"
DEFAULT_SOCKET_PORT = 5001
DEFAULT_API_HOST = "0.0.0.0"
DEFAULT_API_PORT = 8000
