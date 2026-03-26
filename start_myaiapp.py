import os
import sys
import subprocess
import pystray
from PIL import Image, ImageDraw

def create_image(width, height, color1, color2):
    """Generates a default checkerboard icon for the system tray."""
    image = Image.new('RGB', (width, height), color1)
    dc = ImageDraw.Draw(image)
    dc.rectangle((width // 2, 0, width, height // 2), fill=color2)
    dc.rectangle((0, height // 2, width // 2, height), fill=color2)
    return image

# Track background processes to kill them on quit
processes = []

def start_services():
    # Hide the console window exclusively on Windows to ensure it runs silently in the background
    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NO_WINDOW
        
    env = os.environ.copy()
    
    # Use the specific python executable from the virtual environment
    python_exe = sys.executable 
    
    print("Starting API Server...")
    server_proc = subprocess.Popen(
        [python_exe, "main_agent/server.py"],
        creationflags=creationflags,
        env=env
    )
    processes.append(server_proc)
    
    print("Starting Desktop Hotkey Daemon...")
    daemon_proc = subprocess.Popen(
        [python_exe, "desktop_daemon.py"],
        creationflags=creationflags,
        env=env
    )
    processes.append(daemon_proc)

def stop_services(icon, item):
    print("Shutting down MyAIAgent services...")
    icon.stop() # Stops the tray icon loop
    
    for p in processes:
        p.terminate()
        
    sys.exit(0)

def main():
    print("MyAIAgent is starting in the background...")
    start_services()
    
    # Create the system tray menu and icon
    icon_image = create_image(64, 64, '#1b1b24', '#7aa2f7') # Slate Grey / Blue (sleek aesthetic)
    menu = pystray.Menu(
        pystray.MenuItem("🤖 MyAIAgent is Online", lambda: None, enabled=False),
        pystray.MenuItem("Quit", stop_services)
    )
    
    icon = pystray.Icon("myaiapp", icon_image, "MyAIAgent", menu)
    
    # Run the tray icon (this prevents the script from closing and handles tray events)
    icon.run()

if __name__ == "__main__":
    main()
