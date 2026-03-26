import tkinter as tk
from tkinter import ttk
import textwrap

class ModernPopup:
    def __init__(self, title, text, duration_ms=15000):
        self.root = tk.Tk()
        self.root.overrideredirect(True) # Borderless
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.95)
        
        # Colors
        bg_color = "#1e1e2e"
        fg_color = "#cdd6f4"
        accent_color = "#cba6f7"
        
        self.root.configure(bg=bg_color)
        
        # Wrapper frame for a soft border
        main_frame = tk.Frame(self.root, bg=bg_color, highlightbackground=accent_color, highlightthickness=1)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Title
        title_lbl = tk.Label(main_frame, text=title, font=("Segoe UI", 12, "bold"), 
                             bg=bg_color, fg=accent_color, anchor="w", padx=15, pady=8)
        title_lbl.pack(fill=tk.X)
        
        # Close button (top right style via packing)
        close_btn = tk.Label(main_frame, text="✕", font=("Segoe UI", 12), 
                             bg=bg_color, fg="#f38ba8", cursor="hand2")
        close_btn.place(relx=1.0, rely=0.0, x=-10, y=5, anchor="ne")
        close_btn.bind("<Button-1>", lambda e: self.close())
        
        # Separator
        ttk.Separator(main_frame, orient='horizontal').pack(fill=tk.X, padx=10)
        
        # Format text to wrap
        wrapped_text = "\n".join(textwrap.wrap(text, width=60))
        
        # Content
        content_lbl = tk.Label(main_frame, text=wrapped_text, font=("Segoe UI", 10),
                               bg=bg_color, fg=fg_color, justify=tk.LEFT, padx=15, pady=10)
        content_lbl.pack(fill=tk.BOTH, expand=True)
        
        self.root.update_idletasks() # Calculate geometry
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        
        # Position bottom right above taskbar
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = screen_width - width - 20
        y = screen_height - height - 60
        
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        # Bind ESC or click to close
        self.root.bind("<Escape>", lambda e: self.close())
        self.root.bind("<Button-1>", lambda e: self.close())
        
        # Auto-close after duration
        if duration_ms > 0:
            self.root.after(duration_ms, self.close)

    def show(self):
        # Force window to foreground
        self.root.lift()
        self.root.focus_force()
        self.root.mainloop()
        
    def close(self):
        self.root.destroy()

def show_popup(title, message):
    popup = ModernPopup(title, message)
    popup.show()

if __name__ == "__main__":
    show_popup("MyAIAgent", "This is a test explanation. It shows up cleanly on the desktop with no window borders.")
