import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from tkinter import messagebox
import logging
import sys
import os
from utm_controller import UTMController
import tkinter.font as tkFont



# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('utm_controller.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

def main():
    """Main application entry point"""
    try:
        # Create root window
        root = ttk.Window(themename="flatly")

        root.title("UTM Controller - Universal Testing Machine")
        root.geometry("800x600")
        root.resizable(True, True)
        
        # Set window icon and styling
        root.configure(bg='#f0f0f0')
        
        # Ensure window appears on top and is visible
        root.lift()
        root.attributes('-topmost', True)
        root.after_idle(lambda: root.attributes('-topmost', False))
        
        # Create and start the UTM controller
        controller = UTMController(root)
        
        # Handle window close event
        def on_closing():
            try:
                controller.shutdown()
                root.destroy()
            except Exception as e:
                logging.error(f"Error during shutdown: {e}")
                root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Start the application
        logging.info("Starting UTM Controller Application")
        root.mainloop()
        
    except Exception as e:
        logging.error(f"Fatal error starting application: {e}")
        messagebox.showerror("Fatal Error", f"Failed to start application:\n{e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
