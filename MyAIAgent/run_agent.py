import uvicorn
import os
import sys

def main():
    print("Starting Local AI Agent System...")
    print("Main Agent: ONLINE (Background)")
    print("Sub Agent: ONLINE (Google Explainer)")
    print("Server: http://localhost:8000")
    print("\nPress Ctrl+C to stop.")
    
    # Ensure the sandbox directory exists
    os.makedirs("sandbox", exist_ok=True)
    
    # Run the server
    uvicorn.run("main_agent.server:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    main()
