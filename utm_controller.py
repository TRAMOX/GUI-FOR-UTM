"""
UTM Controller - Main application controller class
Handles GUI creation, event management, and coordination between components
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import logging
from serial_handler import SerialHandler
from gui_components import UTMControlPanel, StatusPanel, DataPanel
from graph_plotter import MaterialTestPlotter
from config import UTMConfig
import utils

class UTMController:
    """Main controller class for the UTM application"""
    
    def __init__(self, root):
        self.root = root
        self.config = UTMConfig()
        self.serial_handler = SerialHandler()
        self.running = True
        
        # Machine state variables
        self.machine_state = "Disconnected"
        self.load_value = 0.0
        self.position_value = 0.0
        self.is_connected = False
        
        # Threading events
        self.stop_event = threading.Event()
        
        # Setup GUI
        self.setup_gui()
        
        # Start background threads
        self.start_background_threads()
        
        # Setup serial event callbacks
        self.setup_serial_callbacks()
    
    def setup_gui(self):
        """Initialize and setup the GUI components"""
        try:
            # Create main frame structure
            self.create_main_layout()
            
            # Initialize GUI components
            self.control_panel = UTMControlPanel(self.control_frame, self)
            self.status_panel = StatusPanel(self.status_frame, self)
            self.data_panel = DataPanel(self.data_frame, self)
            self.graph_plotter = MaterialTestPlotter(self.graph_frame, self)
            
            # Setup menu bar
            self.create_menu_bar()
            
            logging.info("GUI components initialized successfully")
            
        except Exception as e:
            logging.error(f"Error setting up GUI: {e}")
            raise
    
    def create_main_layout(self):
        """Create the main window layout structure"""
        # Main container with padding
        main_container = ttk.Frame(self.root, padding="10")
        main_container.grid(row=0, column=0, sticky="nsew")
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_container.columnconfigure(1, weight=1)
        main_container.rowconfigure(1, weight=1)
        
        # Control panel (left side)
        self.control_frame = ttk.LabelFrame(main_container, text="Machine Control", padding="10")
        self.control_frame.grid(row=0, column=0, rowspan=3, sticky="nsew", padx=(0, 10))
        
        # Status panel (top right)
        self.status_frame = ttk.LabelFrame(main_container, text="Status & Connection", padding="5")
        self.status_frame.grid(row=0, column=1, sticky="nsew", pady=(0, 5))
        
        # Data panel (middle right)
        self.data_frame = ttk.LabelFrame(main_container, text="Real-time Data", padding="5")
        self.data_frame.grid(row=1, column=1, sticky="nsew", pady=(0, 5))
        
        # Graph plotting panel (bottom right, larger)
        self.graph_frame = ttk.LabelFrame(main_container, text="Material Testing Analysis", padding="5")
        self.graph_frame.grid(row=2, column=1, sticky="nsew", pady=(0, 0))
        
        # Configure row weights for better resizing
        main_container.rowconfigure(0, weight=1)
        main_container.rowconfigure(1, weight=1)
        main_container.rowconfigure(2, weight=3)  # Graph panel gets more space
    
    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Export Data", command=self.export_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.shutdown)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Refresh COM Ports", command=self.refresh_com_ports)
        tools_menu.add_command(label="Test Connection", command=self.test_connection)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
    
    def setup_serial_callbacks(self):
        """Setup callbacks for serial communication events"""
        self.serial_handler.set_data_callback(self.handle_serial_data)
        self.serial_handler.set_connection_callback(self.handle_connection_change)
    
    def start_background_threads(self):
        """Start background monitoring threads"""
        # Serial monitoring thread
        self.serial_thread = threading.Thread(target=self.serial_monitor_loop, daemon=True)
        self.serial_thread.start()
        
        # GUI update thread
        self.gui_thread = threading.Thread(target=self.gui_update_loop, daemon=True)
        self.gui_thread.start()
        
        logging.info("Background threads started")
    
    def serial_monitor_loop(self):
        """Background thread for monitoring serial communication"""
        while self.running and not self.stop_event.is_set():
            try:
                if self.serial_handler.is_connected():
                    self.serial_handler.read_data()
                time.sleep(0.1)  # 10Hz update rate
            except Exception as e:
                logging.error(f"Error in serial monitor loop: {e}")
                time.sleep(1)
    
    def gui_update_loop(self):
        """Background thread for updating GUI elements"""
        while self.running and not self.stop_event.is_set():
            try:
                # Schedule GUI updates on main thread
                self.root.after_idle(self.update_gui_elements)
                time.sleep(0.2)  # 5Hz update rate
            except Exception as e:
                logging.error(f"Error in GUI update loop: {e}")
                time.sleep(1)
    
    def update_gui_elements(self):
        """Update GUI elements (called on main thread)"""
        try:
            # Update connection status
            self.status_panel.update_connection_status(self.is_connected)
            
            # Update machine state
            self.status_panel.update_machine_state(self.machine_state)
            
            # Update data displays
            self.data_panel.update_load_display(self.load_value)
            self.data_panel.update_position_display(self.position_value)
            
        except Exception as e:
            logging.error(f"Error updating GUI elements: {e}")
    
    def handle_serial_data(self, data):
        """Handle incoming serial data from Arduino"""
        try:
            # Parse incoming data
            if data.startswith('LOAD:'):
                self.load_value = float(data.split(':')[1])
            elif data.startswith('POS:'):
                self.position_value = float(data.split(':')[1])
            elif data.startswith('STATE:'):
                self.machine_state = data.split(':')[1]
            elif data.startswith('BTN:'):
                # Handle PCB button press
                button_code = data.split(':')[1]
                self.handle_pcb_button(button_code)
            elif data.startswith('SPEED:'):
                # Handle speed response from Arduino
                speed_value = int(data.split(':')[1])
                self.handle_speed_response(speed_value)
            
            # Update GUI displays
            if hasattr(self.data_panel, 'update_load_display'):
                self.data_panel.update_load_display(self.load_value)
                
            if hasattr(self.data_panel, 'update_position_display'):
                self.data_panel.update_position_display(self.position_value)
            
            # Send data to graph plotter if plotting is active
            if hasattr(self.graph_plotter, 'is_plotting') and self.graph_plotter.is_plotting:
                import time
                timestamp = time.time()
                self.graph_plotter.add_data_point(timestamp, self.load_value, self.position_value)
            
            logging.debug(f"Processed serial data: {data}")
            
        except Exception as e:
            logging.error(f"Error processing serial data '{data}': {e}")
    
    def handle_pcb_button(self, button_code):
        """Handle physical button press from PCB"""
        try:
            button_map = {
                '1': self.open_command,
                '2': self.close_command,
                '3': self.stop_command,
                '4': self.zero_command
            }
            
            if button_code in button_map:
                # Highlight corresponding GUI button
                self.control_panel.highlight_button(button_code)
                # Execute command
                button_map[button_code]()
                logging.info(f"PCB button {button_code} pressed")
            
        except Exception as e:
            logging.error(f"Error handling PCB button {button_code}: {e}")
    
    def handle_connection_change(self, connected):
        """Handle serial connection status change"""
        self.is_connected = connected
        if connected:
            self.machine_state = "Connected"
            logging.info("Serial connection established")
        else:
            self.machine_state = "Disconnected"
            logging.warning("Serial connection lost")
    
    # Command methods
    def connect_serial(self, port):
        """Connect to serial port"""
        try:
            success = self.serial_handler.connect(port)
            if success:
                messagebox.showinfo("Connection", f"Connected to {port}")
                return True
            else:
                messagebox.showerror("Connection Error", f"Failed to connect to {port}")
                return False
        except Exception as e:
            logging.error(f"Error connecting to {port}: {e}")
            messagebox.showerror("Connection Error", f"Error connecting to {port}:\n{e}")
            return False
    
    def disconnect_serial(self):
        """Disconnect from serial port"""
        try:
            self.serial_handler.disconnect()
            messagebox.showinfo("Connection", "Disconnected from serial port")
        except Exception as e:
            logging.error(f"Error disconnecting: {e}")
    
    def turboset_command(self):
        """Execute Turboset automated routine"""
        try:
            if not self.is_connected:
                messagebox.showerror("Error", "Not connected to Arduino")
                return
            
            # Confirm action
            if messagebox.askyesno("Confirm", "Start Turboset automated routine?"):
                self.serial_handler.send_command('T')
                self.machine_state = "Turboset Running"
                logging.info("Turboset command sent")
        except Exception as e:
            logging.error(f"Error executing Turboset: {e}")
            messagebox.showerror("Error", f"Turboset command failed:\n{e}")
    
    def open_command(self):
        """Send open command to Arduino"""
        try:
            if self.is_connected:
                self.serial_handler.send_command('1')
                self.machine_state = "Opening"
                logging.info("Open command sent")
            else:
                messagebox.showerror("Error", "Not connected to Arduino")
        except Exception as e:
            logging.error(f"Error sending open command: {e}")
    
    def close_command(self):
        """Send close command to Arduino"""
        try:
            if self.is_connected:
                self.serial_handler.send_command('2')
                self.machine_state = "Closing"
                logging.info("Close command sent")
            else:
                messagebox.showerror("Error", "Not connected to Arduino")
        except Exception as e:
            logging.error(f"Error sending close command: {e}")
    
    def stop_command(self):
        """Send stop command to Arduino"""
        try:
            if self.is_connected:
                self.serial_handler.send_command('0')
                self.machine_state = "Stopped"
                logging.info("Stop command sent")
            else:
                messagebox.showerror("Error", "Not connected to Arduino")
        except Exception as e:
            logging.error(f"Error sending stop command: {e}")
    
    def zero_command(self):
        """Send zero/tare command to Arduino"""
        try:
            if self.is_connected:
                self.serial_handler.send_command('Z')
                logging.info("Zero/Tare command sent")
            else:
                messagebox.showerror("Error", "Not connected to Arduino")
        except Exception as e:
            logging.error(f"Error sending zero command: {e}")
    
    # Utility methods
    def refresh_com_ports(self):
        """Refresh available COM ports"""
        try:
            ports = utils.get_available_ports()
            self.status_panel.update_port_list(ports)
            logging.info(f"Refreshed COM ports: {ports}")
        except Exception as e:
            logging.error(f"Error refreshing COM ports: {e}")
    
    def test_connection(self):
        """Test current serial connection"""
        try:
            if self.is_connected:
                # Send test command
                self.serial_handler.send_command('TEST')
                messagebox.showinfo("Test", "Test command sent")
            else:
                messagebox.showwarning("Test", "No active connection to test")
        except Exception as e:
            logging.error(f"Error testing connection: {e}")
            messagebox.showerror("Test Error", f"Connection test failed:\n{e}")
    
    def export_data(self):
        """Export collected data to file"""
        try:
            # Implementation for data export
            messagebox.showinfo("Export", "Data export feature coming soon")
        except Exception as e:
            logging.error(f"Error exporting data: {e}")
    
    def show_about(self):
        """Show about dialog"""
        about_text = """UTM Controller v1.0
        
Universal Testing Machine Control Software
Advanced Python GUI for Arduino-based UTM control

Features:
- Real-time machine control
- Bidirectional PCB communication
- Automated Turboset routines
- Live data monitoring
- Professional industrial interface

© 2024 UTM Controller Application"""
        
        messagebox.showinfo("About UTM Controller", about_text)
    
    def send_custom_command(self, command):
        """Send custom command to Arduino"""
        try:
            if self.serial_handler.is_connected():
                self.serial_handler.send_command(command)
                logging.info(f"Sent custom command: {command}")
            else:
                messagebox.showwarning("Not Connected", "Please connect to a device first")
        except Exception as e:
            logging.error(f"Error sending custom command: {e}")
            messagebox.showerror("Command Error", f"Error sending command: {e}")
    
    def handle_speed_response(self, speed_value):
        """Handle speed response from Arduino"""
        try:
            if hasattr(self.control_panel, 'update_current_speed'):
                self.control_panel.update_current_speed(speed_value)
        except Exception as e:
            logging.error(f"Error handling speed response: {e}")
    
    def shutdown(self):
        """Safely shutdown the application"""
        try:
            logging.info("Shutting down UTM Controller")
            
            # Stop graph plotting
            if hasattr(self.graph_plotter, 'stop_plotting'):
                self.graph_plotter.stop_plotting()
            
            # Stop background threads
            self.running = False
            self.stop_event.set()
            
            # Disconnect serial
            if self.serial_handler.is_connected():
                self.serial_handler.disconnect()
            
            # Close GUI
            self.root.quit()
            
        except Exception as e:
            logging.error(f"Error during shutdown: {e}")
