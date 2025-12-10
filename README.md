📘 EcoBot — Chatbot Económico Multi-Sesión (Servidor Socket + Groq)

EcoBot es un chatbot especializado en responder preguntas de economía, potenciando modelos LLM de Groq.
Funciona como un servidor TCP multi-usuario donde cada conexión representa una sesión independiente, con historial propio y administración en tiempo real.

🚀 Características principales
🧠 Multi-sesión real

Cada conexión TCP crea una sesión independiente.

Memoria por conversación en el servidor.

Manejo concurrente utilizando threads.

Identificador humano: Sesión 1, Sesión 2, etc.

Identificador técnico: session_id corto (ej. 91ab27ef).

💬 Conversación inteligente

EcoBot puede:

Responder preguntas teóricas de economía.

Realizar cálculos sencillos.

Generar interpretaciones basadas en conocimiento incluido en el router.

Consultar modelos LLM de Groq para consultas complejas.

🧰 Consola Administrativa integrada

Incluye una consola interactiva para gestionar sesiones activas:

list                → ver todas las sesiones activas
kill <session_id>   → cerrar una sesión específica
exit                → cerrar la consola admin (el servidor sigue corriendo)

🔌 Cliente TCP simple

Se incluye un cliente para pruebas desde consola.

📦 Estructura del Proyecto
EcoBot/
│
├── app/
│   ├── server_socket.py     # Servidor TCP multi-sesión
│   ├── socket_client.py     # Cliente TCP de prueba
│   ├── router.py            # Lógica de enrutamiento y llamadas a Groq
│   ├── ...
│
├── requirements.txt
└── README.md

⚙️ Requisitos Previos
Python 3.10+
Instalar dependencias
pip install -r requirements.txt

Variables de entorno
GROQ_API_KEY="tu_api_key_aquí"
ECOBOT_SOCKET_PORT=5001

🟦 Cómo ejecutar el Servidor Socket

Desde la carpeta raíz del proyecto:

python -m app.server_socket


Verás algo como:

EcoBot socket server escuchando en 0.0.0.0:5001 ...
Consola admin lista. Comandos: list, kill <session_id>, exit
(admin)>


Cuando un cliente se conecta:

[Sesión 1] Nueva conexión desde ('127.0.0.1', 53294) (sid=91ab27ef)

🛠️ Comandos de la Consola Admin

Usás la misma terminal donde corre el servidor.

Ver sesiones activas:
(admin)> list
Sesión 1 (91ab27ef) | ('127.0.0.1', 53294) | hilo=handle_client | started=... | last_seen=...

Cerrar una sesión:
(admin)> kill 91ab27ef
Sesión 91ab27ef cerrada desde admin.

Salir de la consola admin:
(admin)> exit


El servidor continúa corriendo en segundo plano.

🟩 Cliente TCP de Prueba

En otra terminal:

python app/socket_client.py


Ejemplo de interacción:

Bienvenido a EcoBot👋
Tu session_id es: 91ab27ef
Escribí tu pregunta de economía o 'salir' para desconectarte.

> ¿Qué es el PBI?
EcoBot: El Producto Bruto Interno es...

🧱 Cómo funciona internamente
1. Cada cliente crea una nueva sesión

Con:

session_id = uuid.uuid4().hex[:8]
session_number = next(SESSION_SEQ)

2. Se registra la sesión activa
active_connections[session_id] = {
    "addr": ("127.0.0.1", 53294),
    "thread": "handle_client",
    "started_at": "...",
    "last_seen": "...",
    "number": 1,
    "conn": <socket>
}

3. Historial de conversación independiente
SESSION_HISTORIES[session_id] = [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
]

4. Manejo concurrente

Cada conexión se maneja en su propio thread, protegido por locks para evitar condiciones de carrera. 🧹 Notas importantes

El historial se guarda en memoria RAM; se borra al reiniciar el servidor.

El servidor puede manejar múltiples usuarios concurrentes.

Para miles de usuarios o persistencia, debería agregarse almacenamiento externo (no incluido).
