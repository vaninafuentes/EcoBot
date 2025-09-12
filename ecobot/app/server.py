from rich.console import Console
from app.config import BOT_NAME, BOT_VERSION
from app.router import route_question

console = Console()

def main():
    console.print(f"[bold green]{BOT_NAME} v{BOT_VERSION}[/bold green]")
    console.print("Charla abierta (económica por defecto). Escribí 'salir' para terminar.\n")

    history = []  # <- guardamos el hilo: [{"role": "user"/"assistant", "content": "..."}]

    while True:
        question = console.input("[bold blue]Tú[/bold blue]: ")
        if question.strip().lower() in {"salir", "exit", "quit"}:
            console.print("[red]Cerrando EcoBot...[/red]")
            break

        answer = route_question(question, history=history)
        console.print(f"[bold green]{BOT_NAME}[/bold green]: {answer}\n")

        # actualizar memoria corta
        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": answer})

if __name__ == "__main__":
    main()
