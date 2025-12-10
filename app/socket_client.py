import socket

HOST = "localhost"
PORT = 5001

with socket.create_connection((HOST, PORT)) as s:
    while True:
        data = s.recv(4096)
        if not data:
            break
        print(data.decode("utf-8"), end="")
        msg = input()
        s.sendall((msg + "\n").encode("utf-8"))
        if msg.lower() in {"salir", "exit", "quit"}:
            break
