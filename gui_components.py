"""
GUI Components - Individual UI components for the UTM Controller
Modular GUI elements for better organization and maintainability
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
import utils

class UTMControlPanel:
    """Control panel with all machine control buttons"""
    
    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller
        self.button_refs = {}
        self.setup_controls()
    
    def setup_controls(self):
        """Setup control panel UI elements"""
        # Connection section
        self.create_connection_section()
        
        # Separator
        ttk.Separator(self.parent, orient='horizontal').pack(fill='x', pady=10)
        
        # Main control buttons
        self.create_main_controls()
        
        # Separator
        ttk.Separator(self.parent, orient='horizontal').pack(fill='x', pady=10)
        
        # Manual control buttons
        self.create_manual_controls()
        
        # Separator
        ttk.Separator(self.parent, orient='horizontal').pack(fill='x', pady=10)
        
        # Speed control section
        self.create_speed_controls()
    
    def create_connection_section(self):
        """Create connection controls"""
        conn_frame = ttk.Frame(self.parent)
        conn_frame.pack(fill='x', pady=5)
        
        # COM Port selection
        ttk.Label(conn_frame, text="COM Port:").pack(anchor='w')
        
        port_frame = ttk.Frame(conn_frame)
        port_frame.pack(fill='x', pady=2)
        
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(port_frame, textvariable=self.port_var, 
                                      state="readonly", width=15)
        self.port_combo.pack(side='left', padx=(0, 5))
        
        # Refresh ports button
        refresh_btn = ttk.Button(port_frame, text="🔄", width=3,
                               command=self.refresh_ports)
        refresh_btn.pack(side='left')
        
        # Connect/Disconnect buttons
        btn_frame = ttk.Frame(conn_frame)
        btn_frame.pack(fill='x', pady=5)
        
        self.connect_btn = ttk.Button(btn_frame, text="Connect",
                                    command=self.connect_clicked)
        self.connect_btn.pack(side='left', padx=(0, 5))
        
        self.disconnect_btn = ttk.Button(btn_frame, text="Disconnect",
                                       command=self.disconnect_clicked,
                                       state='disabled')
        self.disconnect_btn.pack(side='left')
        
        # Load available ports
        self.refresh_ports()
    
    def create_main_controls(self):
        """Create main control buttons"""
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill='x', pady=5)
        
        ttk.Label(main_frame, text="Main Controls:", font=('Arial', 10, 'bold')).pack(anchor='w')
        
        # Turboset button (prominent)
        self.turboset_btn = ttk.Button(main_frame, text="🚀 Open using Turboset",
                                     command=self.controller.turboset_command,
                                     style='Accent.TButton')
        self.turboset_btn.pack(fill='x', pady=5)
        self.button_refs['T'] = self.turboset_btn
    
    def create_manual_controls(self):
        """Create manual control buttons"""
        manual_frame = ttk.Frame(self.parent)
        manual_frame.pack(fill='x', pady=5)
        
        ttk.Label(manual_frame, text="Manual Controls:", font=('Arial', 10, 'bold')).pack(anchor='w')
        
        # Button grid
        btn_grid = ttk.Frame(manual_frame)
        btn_grid.pack(fill='x', pady=5)
        
        # Configure grid
        btn_grid.columnconfigure(0, weight=1)
        btn_grid.columnconfigure(1, weight=1)
        
        # Open button
        self.open_btn = ttk.Button(btn_grid, text="⬆ Open",
                                 command=self.controller.open_command)
        self.open_btn.grid(row=0, column=0, sticky='ew', padx=(0, 2), pady=2)
        self.button_refs['1'] = self.open_btn
        
        # Close button
        self.close_btn = ttk.Button(btn_grid, text="⬇ Close",
                                  command=self.controller.close_command)
        self.close_btn.grid(row=0, column=1, sticky='ew', padx=(2, 0), pady=2)
        self.button_refs['2'] = self.close_btn
        
        # Stop button (full width)
        self.stop_btn = ttk.Button(btn_grid, text="🛑 STOP",
                                 command=self.controller.stop_command)
        self.stop_btn.grid(row=1, column=0, columnspan=2, sticky='ew', pady=2)
        self.button_refs['3'] = self.stop_btn
        
        # Zero button (full width)
        self.zero_btn = ttk.Button(btn_grid, text="⚖ Zero/Tare",
                                 command=self.controller.zero_command)
        self.zero_btn.grid(row=2, column=0, columnspan=2, sticky='ew', pady=2)
        self.button_refs['4'] = self.zero_btn
    
    def refresh_ports(self):
        """Refresh available COM ports"""
        try:
            ports = utils.get_available_ports()
            port_names = [port['device'] for port in ports]
            self.port_combo['values'] = port_names
            
            if port_names and not self.port_var.get():
                self.port_var.set(port_names[0])
                
        except Exception as e:
            logging.error(f"Error refreshing ports: {e}")
            messagebox.showerror("Error", f"Failed to refresh COM ports:\n{e}")
    
    def connect_clicked(self):
        """Handle connect button click"""
        try:
            port = self.port_var.get()
            if not port:
                messagebox.showerror("Error", "Please select a COM port")
                return
            
            if self.controller.connect_serial(port):
                self.connect_btn.config(state='disabled')
                self.disconnect_btn.config(state='normal')
                self.port_combo.config(state='disabled')
                
        except Exception as e:
            logging.error(f"Error in connect clicked: {e}")
    
    def disconnect_clicked(self):
        """Handle disconnect button click"""
        try:
            self.controller.disconnect_serial()
            self.connect_btn.config(state='normal')
            self.disconnect_btn.config(state='disabled')
            self.port_combo.config(state='readonly')
            
        except Exception as e:
            logging.error(f"Error in disconnect clicked: {e}")
    
    def highlight_button(self, button_code):
        """Highlight button corresponding to PCB button press"""
        try:
            if button_code in self.button_refs:
                button = self.button_refs[button_code]
                # Flash button to indicate PCB activation
                original_style = button.cget('style')
                button.config(style='Accent.TButton')
                self.parent.after(500, lambda: button.config(style=original_style))
                
        except Exception as e:
            logging.error(f"Error highlighting button {button_code}: {e}")
    
    def create_speed_controls(self):
        """Create stepper motor speed control section"""
        speed_frame = ttk.LabelFrame(self.parent, text="Motor Speed Control", padding="5")
        speed_frame.pack(fill='x', pady=5)
        
        # Current speed display
        current_speed_frame = ttk.Frame(speed_frame)
        current_speed_frame.pack(fill='x', pady=2)
        
        ttk.Label(current_speed_frame, text="Current Speed:").pack(side='left')
        self.current_speed_var = tk.StringVar(value="10 RPM")
        ttk.Label(current_speed_frame, textvariable=self.current_speed_var, 
                 font=('Arial', 10, 'bold')).pack(side='left', padx=10)
        
        # Speed setting
        speed_setting_frame = ttk.Frame(speed_frame)
        speed_setting_frame.pack(fill='x', pady=5)
        
        ttk.Label(speed_setting_frame, text="Set Speed (RPM):").pack(side='left')
        
        self.speed_var = tk.DoubleVar(value=10.0)
        self.speed_scale = ttk.Scale(speed_setting_frame, from_=1, to=200, 
                                   orient='horizontal', variable=self.speed_var,
                                   length=200)
        self.speed_scale.pack(side='left', padx=5)
        
        self.speed_entry = ttk.Entry(speed_setting_frame, textvariable=self.speed_var, width=8)
        self.speed_entry.pack(side='left', padx=5)
        
        # Speed control buttons
        speed_buttons_frame = ttk.Frame(speed_frame)
        speed_buttons_frame.pack(fill='x', pady=5)
        
        self.set_speed_btn = ttk.Button(speed_buttons_frame, text="Set Speed", 
                                      command=self.set_motor_speed)
        self.set_speed_btn.pack(side='left', padx=2)
        
        self.get_speed_btn = ttk.Button(speed_buttons_frame, text="Get Speed", 
                                      command=self.get_motor_speed)
        self.get_speed_btn.pack(side='left', padx=2)
        
        # Preset speeds
        preset_frame = ttk.Frame(speed_frame)
        preset_frame.pack(fill='x', pady=2)
        
        ttk.Label(preset_frame, text="Presets:").pack(side='left')
        
        preset_speeds = [1, 5, 10, 25, 50, 100]
        for speed in preset_speeds:
            btn = ttk.Button(preset_frame, text=f"{speed}", width=4,
                           command=lambda s=speed: self.set_preset_speed(s))
            btn.pack(side='left', padx=1)
    
    def set_motor_speed(self):
        """Send set speed command to Arduino"""
        try:
            speed = int(self.speed_var.get())
            if 1 <= speed <= 200:
                command = f"S{speed}"
                self.controller.send_custom_command(command)
                self.current_speed_var.set(f"{speed} RPM")
                logging.info(f"Set motor speed to {speed} RPM")
            else:
                messagebox.showwarning("Invalid Speed", "Speed must be between 1 and 200 RPM")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number")
        except Exception as e:
            logging.error(f"Error setting motor speed: {e}")
    
    def get_motor_speed(self):
        """Get current motor speed from Arduino"""
        try:
            self.controller.send_custom_command("G")
            logging.info("Requested current motor speed")
        except Exception as e:
            logging.error(f"Error getting motor speed: {e}")
    
    def set_preset_speed(self, speed):
        """Set a preset speed value"""
        self.speed_var.set(speed)
        self.set_motor_speed()
    
    def update_current_speed(self, speed):
        """Update the current speed display"""
        self.current_speed_var.set(f"{speed} RPM")

class StatusPanel:
    """Status and connection information panel"""
    
    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller
        self.setup_status_display()
    
    def setup_status_display(self):
        """Setup status display elements"""
        # Connection status
        conn_frame = ttk.Frame(self.parent)
        conn_frame.pack(fill='x', pady=5)
        
        ttk.Label(conn_frame, text="Connection Status:", font=('Arial', 10, 'bold')).pack(anchor='w')
        
        self.conn_status_var = tk.StringVar(value="Disconnected")
        self.conn_status_label = ttk.Label(conn_frame, textvariable=self.conn_status_var,
                                         foreground='red')
        self.conn_status_label.pack(anchor='w', padx=10)
        
        # Machine state
        state_frame = ttk.Frame(self.parent)
        state_frame.pack(fill='x', pady=5)
        
        ttk.Label(state_frame, text="Machine State:", font=('Arial', 10, 'bold')).pack(anchor='w')
        
        self.machine_state_var = tk.StringVar(value="Idle")
        self.machine_state_label = ttk.Label(state_frame, textvariable=self.machine_state_var,
                                           font=('Arial', 12, 'bold'))
        self.machine_state_label.pack(anchor='w', padx=10)
        
        # Additional info
        info_frame = ttk.Frame(self.parent)
        info_frame.pack(fill='x', pady=5)
        
        ttk.Label(info_frame, text="System Info:", font=('Arial', 10, 'bold')).pack(anchor='w')
        
        self.info_text = tk.Text(info_frame, height=4, wrap='word', state='disabled')
        self.info_text.pack(fill='both', expand=True, padx=10)
        
        # Scrollbar for info text
        scrollbar = ttk.Scrollbar(info_frame, orient='vertical', command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
    
    def update_connection_status(self, connected):
        """Update connection status display"""
        if connected:
            self.conn_status_var.set("Connected")
            self.conn_status_label.config(foreground='green')
        else:
            self.conn_status_var.set("Disconnected")
            self.conn_status_label.config(foreground='red')
    
    def update_machine_state(self, state):
        """Update machine state display"""
        self.machine_state_var.set(state)
        
        # Color code based on state
        color_map = {
            'Connected': 'green',
            'Disconnected': 'red',
            'Opening': 'blue',
            'Closing': 'blue',
            'Stopped': 'orange',
            'Turboset Running': 'purple',
            'Error': 'red'
        }
        
        color = color_map.get(state, 'black')
        self.machine_state_label.config(foreground=color)
    
    def update_port_list(self, ports):
        """Update system info with available ports"""
        info_text = "Available COM Ports:\n"
        for port in ports:
            info_text += f"  {port['device']}: {port['description']}\n"
        
        self.info_text.config(state='normal')
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, info_text)
        self.info_text.config(state='disabled')

class DataPanel:
    """Real-time data display panel"""
    
    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller
        self.setup_data_display()
    
    def setup_data_display(self):
        """Setup data display elements"""
        # Load/Force display
        load_frame = ttk.Frame(self.parent)
        load_frame.pack(fill='x', pady=5)
        
        ttk.Label(load_frame, text="Load/Force:", font=('Arial', 10, 'bold')).pack(anchor='w')
        
        self.load_var = tk.StringVar(value="0.00 N")
        load_display = ttk.Label(load_frame, textvariable=self.load_var,
                               font=('Arial', 16, 'bold'), foreground='blue')
        load_display.pack(anchor='w', padx=10)
        
        # Position display
        pos_frame = ttk.Frame(self.parent)
        pos_frame.pack(fill='x', pady=5)
        
        ttk.Label(pos_frame, text="Position:", font=('Arial', 10, 'bold')).pack(anchor='w')
        
        self.position_var = tk.StringVar(value="0.00 mm")
        pos_display = ttk.Label(pos_frame, textvariable=self.position_var,
                              font=('Arial', 14), foreground='green')
        pos_display.pack(anchor='w', padx=10)
        
        # Data logging controls
        log_frame = ttk.Frame(self.parent)
        log_frame.pack(fill='x', pady=10)
        
        ttk.Label(log_frame, text="Data Logging:", font=('Arial', 10, 'bold')).pack(anchor='w')
        
        log_btn_frame = ttk.Frame(log_frame)
        log_btn_frame.pack(fill='x', pady=2)
        
        self.log_btn = ttk.Button(log_btn_frame, text="Start Logging",
                                command=self.toggle_logging)
        self.log_btn.pack(side='left', padx=(10, 5))
        
        self.export_btn = ttk.Button(log_btn_frame, text="Export Data",
                                   command=self.controller.export_data)
        self.export_btn.pack(side='left')
        
        # Data statistics
        stats_frame = ttk.Frame(self.parent)
        stats_frame.pack(fill='x', pady=5)
        
        ttk.Label(stats_frame, text="Statistics:", font=('Arial', 10, 'bold')).pack(anchor='w')
        
        self.stats_text = tk.Text(stats_frame, height=6, wrap='word', state='disabled')
        self.stats_text.pack(fill='both', expand=True, padx=10)
        
        # Initialize with default stats
        self.update_statistics()
    
    def update_load_display(self, load_value):
        """Update load/force display"""
        self.load_var.set(f"{load_value:.2f} N")
    
    def update_position_display(self, position_value):
        """Update position display"""
        self.position_var.set(f"{position_value:.2f} mm")
    
    def toggle_logging(self):
        """Toggle data logging on/off"""
        current_text = self.log_btn.cget('text')
        if current_text == "Start Logging":
            self.log_btn.config(text="Stop Logging")
            logging.info("Data logging started")
        else:
            self.log_btn.config(text="Start Logging")
            logging.info("Data logging stopped")
    
    def update_statistics(self):
        """Update data statistics display"""
        stats_text = """Data Statistics:
  Samples Collected: 0
  Max Load: 0.00 N
  Min Load: 0.00 N
  Avg Load: 0.00 N
  Max Position: 0.00 mm
  Test Duration: 00:00:00"""
        
        self.stats_text.config(state='normal')
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats_text)
        self.stats_text.config(state='disabled')
