from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
import urllib.request
import urllib.error
import json
import sys

console = Console()
SERVER_URL = "http://localhost:8000"

def check_health():
    try:
        req = urllib.request.urlopen(f"{SERVER_URL}/health", timeout=3)
        data = json.loads(req.read())
        if data.get("status") == "running":
            return True
        return False
    except Exception:
        return False

def call_agent(endpoint, payload):
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(f"{SERVER_URL}/{endpoint}", data=data, 
                                 headers={'Content-Type': 'application/json'}, method="POST")
    try:
        response = urllib.request.urlopen(req, timeout=30)
        return json.loads(response.read())
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode('utf-8')
        try:
            return json.loads(error_msg)
        except:
            return {"status": "error", "message": str(e)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def main():
    console.print(Panel.fit("[bold cyan]🤖 MyAIAgent CLI[/bold cyan]\nType [bold green]/quit[/bold green] to exit, [bold yellow]/help[/bold yellow] for commands.", border_style="blue"))
    
    with console.status("[dim]Checking server connection...[/dim]"):
        if not check_health():
            console.print("[red]❌ Cannot connect to MyAIAgent server.[/red]")
            console.print("Please run [bold cyan]python run_agent.py[/bold cyan] in another terminal first.")
            sys.exit(1)
            
    console.print("[green]✅ Server online.[/green]\n")
    
    chat_history = []
    
    while True:
        try:
            user_input = Prompt.ask("\n[bold blue]You[/bold blue]")
        except (KeyboardInterrupt, EOFError):
            break
            
        if not user_input.strip():
            continue
            
        if user_input.lower() in ["/quit", "/exit", "exit"]:
            console.print("[dim]Goodbye![/dim]")
            break
            
        if user_input.lower() == "/help":
            console.print(Panel(
                "/explain <text>   - Get a detailed explanation\n"
                "/summarize <text> - Get bullet points\n"
                "/translate <text> - Translate to Spanish (default)\n"
                "/clear            - Clear chat history\n"
                "/quit             - Exit",
                title="Commands", border_style="yellow"
            ))
            continue
            
        if user_input.lower() == "/clear":
            chat_history = []
            console.print("[dim]Chat history cleared.[/dim]")
            continue
            
        # Parse command VS chat
        action = "chat"
        text = user_input
        endpoint = "chat" # Default agent is Coordinator
        payload = {"text": text}
        
        if user_input.startswith("/explain "):
            text = user_input[9:]
            endpoint = "explain"
            payload = {"text": text, "style": "textbook", "history": []}
            chat_history = [] # Don't pollute chat history with one-off cmds
        elif user_input.startswith("/summarize "):
            text = user_input[11:]
            endpoint = "summarize"
            payload = {"text": text, "length": "short"}
            chat_history = []
        elif user_input.startswith("/translate "):
            text = user_input[11:]
            endpoint = "translate"
            payload = {"text": text, "target_language": "spanish"}
            chat_history = []
        else:
            # Generic chat mode
            chat_history.append({"role": "user", "content": user_input})

        with console.status("[bold cyan]Agent is typing...[/bold cyan]", spinner="dots"):
            response = call_agent(endpoint, payload)
        
        if response.get("status") == "success":
            reply = ""
            if endpoint == "explain":
                reply = response.get("explanation", "")
                if action == "chat":
                    chat_history.append({"role": "model", "content": reply})
            elif endpoint == "chat":
                reply = response.get("response", "")
                if action == "chat":
                    chat_history.append({"role": "model", "content": reply})
            elif endpoint == "summarize":
                reply = response.get("summary", "")
            elif endpoint == "translate":
                reply = response.get("translation", "")
                
            console.print(Panel(Markdown(reply), title="[bold magenta]AI[/bold magenta]", border_style="magenta"))
        else:
            err = response.get("message") or response.get("detail") or "Unknown error"
            console.print(f"[red]Error: {err}[/red]")
            if action == "chat":
                chat_history.pop() # Remove failed msg from history

if __name__ == "__main__":
    main()
