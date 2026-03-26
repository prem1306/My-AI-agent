import keyboard
import pyperclip
import time
import urllib.request
import json
import threading
from ui_popup import show_popup

SERVER_URL = "http://localhost:8000"

def get_explanation(text):
    try:
        data = json.dumps({"text": text, "style": "simple", "history": []}).encode('utf-8')
        req = urllib.request.Request(f"{SERVER_URL}/explain", data=data, 
                                     headers={'Content-Type': 'application/json'}, method="POST")
        response = urllib.request.urlopen(req, timeout=15)
        res_data = json.loads(response.read())
        if res_data.get("status") == "success":
            return res_data.get("explanation", "")
        return f"Error: {res_data.get('message', 'Unknown')}"
    except Exception as e:
        return f"Connection Failed: Is run_agent.py active? ({e})"

def on_hotkey():
    print("Hotkey detected! Grabbing text...")
    
    # Save current clipboard
    old_clipboard = pyperclip.paste()
    pyperclip.copy("")
    
    # Simulate Ctrl+C to copy selected text
    keyboard.send('ctrl+c')
    time.sleep(0.1) # Wait for OS clipboard update
    
    selected_text = pyperclip.paste()
    
    if not selected_text.strip():
        print("No text selected.")
        # Restore old clipboard
        pyperclip.copy(old_clipboard)
        return
        
    print(f"Captured: {selected_text[:50]}...")
    
    # Run API call in a thread so hotkey hook doesn't block
    def process():
        show_popup("MyAIAgent Working...", "Requesting explanation...")
        # The above popup is blocking; we'll show a loading via console and just pop the final.
        pass

    def background_task():
        # Call API
        reply = get_explanation(selected_text)
        print("Reply received. Showing popup.")
        # Restore clipboard so user doesn't lose what they had previously
        pyperclip.copy(old_clipboard)
        # Show final result natively
        show_popup("✨ AI Explanation", reply)
        
    threading.Thread(target=background_task, daemon=True).start()

def main():
    print("====================================")
    print("  MyAIAgent Desktop Daemon Started")
    print("====================================")
    print("Listening for: Ctrl+Alt+A")
    print("Highlight text anywhere and press the hotkey.")
    print("Press Ctrl+C in this terminal to quit.\n")
    
    keyboard.add_hotkey('ctrl+alt+a', on_hotkey)
    
    # Block forever
    keyboard.wait()

if __name__ == "__main__":
    main()
