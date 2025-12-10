🧠 EcoBot — Chatbot Económico Multi-Sesión (Servidor TCP + Groq)

EcoBot es un chatbot especializado en economía que funciona como un servidor TCP multiusuario, donde cada conexión representa una sesión independiente con su propio historial.
Todas las respuestas se generan mediante un router económico y modelos LLM de Groq.

✨ Características Principales

🔌 Servidor TCP Multi-Sesión
Cada conexión crea su propia sesión con historial aislado.

🧠 Respuestas inteligentes
Conocimiento económico + cálculos + llamadas a LLM.

🧰 Consola Administrativa Interna

list → lista sesiones activas

kill <session_id> → cierra una sesión

exit → cierra la consola admin sin apagar el servidor

🧵 Concurrencia por hilos
Cada cliente se maneja en su propio thread.

📜 Historial por sesión
Memoria en RAM, aislada entre usuarios.

📁 Estructura del Proyecto
EcoBot/
│
├── app/
│   ├── server_socket.py     # Servidor TCP multi-usuario
│   ├── socket_client.py     # Cliente para pruebas
│   ├── router.py            # Router económico + Groq
│   └── ...
│
├── requirements.txt
└── README.md

⚙️ Requisitos
🐍 Python 3.10 o superior
📦 Instalar dependencias
pip install -r requirements.txt

🔑 Variables de entorno necesarias
GROQ_API_KEY="TU_API_KEY"
ECOBOT_SOCKET_PORT=5001

🚀 Ejecutar el Servidor Socket

Desde la raíz del proyecto:

python -m app.server_socket


Salida esperada:

EcoBot socket server escuchando en 0.0.0.0:5001 ...
Consola admin lista. Comandos: list, kill <session_id>, exit
(admin)>


Cuando un cliente se conecta:

[Sesión 1] Nueva conexión desde ('127.0.0.1', 53294) (sid=91ab27ef)

🛠 Consola Administrativa

La consola admin está integrada en el mismo proceso del servidor.

📄 Listar sesiones activas
(admin)> list
Sesión 1 (91ab27ef) | ('127.0.0.1', 53294) | hilo=handle_client | started=... | last_seen=...

❌ Cerrar una sesión
(admin)> kill 91ab27ef
Sesión 91ab27ef cerrada desde admin.

🚪 Salir de la consola admin
(admin)> exit


(El servidor sigue funcionando aunque cierres la consola admin.)

🟩 Cliente TCP de prueba

En otra terminal:

python app/socket_client.py


Ejemplo de interacción:

Bienvenido a EcoBot👋
Tu session_id es: 91ab27ef
Escribí tu pregunta de economía o 'salir' para desconectarte.

> ¿Qué es el PBI?
EcoBot: El Producto Bruto Interno es...

🧱 Cómo funciona internamente
🔢 1. Se genera una sesión por conexión
session_id = uuid.uuid4().hex[:8]
session_number = next(SESSION_SEQ)

📌 2. Se guarda en active_connections
{
  "addr": ("127.0.0.1", 53294),
  "thread": "handle_client",
  "started_at": "...",
  "last_seen": "...",
  "number": 1,
  "conn": <socket>
}

📝 3. Historial por sesión
SESSION_HISTORIES[session_id] = [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
]

🧵 4. Cada conexión corre en un hilo independiente

Protegido con locks para evitar condiciones de carrera. 🧹 Consideraciones

El historial se guarda solo en memoria RAM (se pierde al reiniciar).

Ideal para entornos controlados, usos académicos o bots personales.

Para muchos usuarios simultáneos, puede ampliarse con:

Persistencia externa

Multiproceso o asyncio

Logs estructurados
