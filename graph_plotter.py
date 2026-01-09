import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from matplotlib.figure import Figure
import numpy as np
from scipy import stats
import logging
from config import UTMConfig
import utils
import threading
import time
from datetime import datetime

class MaterialTestPlotter:
    
    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller
        self.config = UTMConfig()
        
        # Data storage
        self.time_data = []
        self.load_data = []
        self.position_data = []
        self.stress_data = []
        self.strain_data = []
        self.displacement_data = []
        
        # Test parameters
        self.specimen_area = 1.0  # mm²
        self.gauge_length = 25.0  # mm
        self.material_type = "Steel"
        self.test_mode = "TENSILE"
        
        # Analysis results
        self.youngs_modulus = 0.0
        self.yield_strength = 0.0
        self.ultimate_strength = 0.0
        self.fracture_strength = 0.0
        self.elongation_at_break = 0.0
        
        # Plot settings
        self.is_plotting = False
        self.auto_scale = True
        self.plot_update_thread = None
        
        self.setup_plotter_gui()
        
    def setup_plotter_gui(self):
        # Create notebook for different tabs
        self.notebook = ttk.Notebook(self.parent)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Real-time plots tab
        self.create_realtime_tab()
        
        # Analysis tab
        self.create_analysis_tab()
        
        # Material properties tab
        self.create_properties_tab()
        
    def create_realtime_tab(self):
        self.realtime_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.realtime_frame, text="Real-time Plots")
        
        # Control panel
        control_frame = ttk.Frame(self.realtime_frame)
        control_frame.pack(fill='x', padx=5, pady=5)
        
        # Test parameters
        params_frame = ttk.LabelFrame(control_frame, text="Test Parameters", padding="5")
        params_frame.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        # Specimen area
        ttk.Label(params_frame, text="Cross-sectional Area (mm²):").grid(row=0, column=0, sticky='w', padx=2, pady=2)
        self.area_var = tk.DoubleVar(value=1.0)
        self.area_entry = ttk.Entry(params_frame, textvariable=self.area_var, width=10)
        self.area_entry.grid(row=0, column=1, padx=2, pady=2)
        
        # Gauge length
        ttk.Label(params_frame, text="Gauge Length (mm):").grid(row=1, column=0, sticky='w', padx=2, pady=2)
        self.gauge_var = tk.DoubleVar(value=25.0)
        self.gauge_entry = ttk.Entry(params_frame, textvariable=self.gauge_var, width=10)
        self.gauge_entry.grid(row=1, column=1, padx=2, pady=2)
        
        # Material type
        ttk.Label(params_frame, text="Material:").grid(row=2, column=0, sticky='w', padx=2, pady=2)
        self.material_var = tk.StringVar(value="Steel")
        self.material_combo = ttk.Combobox(params_frame, textvariable=self.material_var, 
                                         values=self.config.MATERIAL_TYPES, state="readonly", width=10)
        self.material_combo.grid(row=2, column=1, padx=2, pady=2)
        
        # Test mode
        ttk.Label(params_frame, text="Test Mode:").grid(row=3, column=0, sticky='w', padx=2, pady=2)
        self.test_mode_var = tk.StringVar(value="TENSILE")
        self.test_mode_combo = ttk.Combobox(params_frame, textvariable=self.test_mode_var,
                                          values=list(self.config.TEST_MODES.keys()), state="readonly", width=10)
        self.test_mode_combo.grid(row=3, column=1, padx=2, pady=2)
        
        # Plot controls
        plot_control_frame = ttk.LabelFrame(control_frame, text="Plot Controls", padding="5")
        plot_control_frame.pack(side='right', padx=(5, 0))
        
        self.start_plot_btn = ttk.Button(plot_control_frame, text="Start Plotting", 
                                       command=self.start_plotting)
        self.start_plot_btn.pack(pady=2)
        
        self.stop_plot_btn = ttk.Button(plot_control_frame, text="Stop Plotting", 
                                      command=self.stop_plotting, state='disabled')
        self.stop_plot_btn.pack(pady=2)
        
        self.clear_plot_btn = ttk.Button(plot_control_frame, text="Clear Data", 
                                       command=self.clear_plot_data)
        self.clear_plot_btn.pack(pady=2)
        
        self.auto_scale_var = tk.BooleanVar(value=True)
        self.auto_scale_check = ttk.Checkbutton(plot_control_frame, text="Auto Scale", 
                                              variable=self.auto_scale_var)
        self.auto_scale_check.pack(pady=2)
        
        # Create matplotlib figure
        self.create_plot_figure()
        
    def create_plot_figure(self):
        # Create figure with subplots
        self.fig = Figure(figsize=(12, 8), dpi=100)
        
        # Create subplots
        self.ax1 = self.fig.add_subplot(2, 2, 1)  # Load vs Time
        self.ax2 = self.fig.add_subplot(2, 2, 2)  # Position vs Time
        self.ax3 = self.fig.add_subplot(2, 2, 3)  # Stress vs Strain
        self.ax4 = self.fig.add_subplot(2, 2, 4)  # Load vs Position
        
        # Set labels
        self.ax1.set_xlabel('Time (s)')
        self.ax1.set_ylabel('Load (N)')
        self.ax1.set_title('Load vs Time')
        self.ax1.grid(True)
        
        self.ax2.set_xlabel('Time (s)')
        self.ax2.set_ylabel('Position (mm)')
        self.ax2.set_title('Position vs Time')
        self.ax2.grid(True)
        
        self.ax3.set_xlabel('Strain (%)')
        self.ax3.set_ylabel('Stress (MPa)')
        self.ax3.set_title('Stress-Strain Curve')
        self.ax3.grid(True)
        
        self.ax4.set_xlabel('Displacement (mm)')
        self.ax4.set_ylabel('Load (N)')
        self.ax4.set_title('Load vs Displacement')
        self.ax4.grid(True)
        
        # Initialize empty plots
        self.line1, = self.ax1.plot([], [], 'b-', linewidth=2)
        self.line2, = self.ax2.plot([], [], 'r-', linewidth=2)
        self.line3, = self.ax3.plot([], [], 'g-', linewidth=2)
        self.line4, = self.ax4.plot([], [], 'm-', linewidth=2)
        
        # Tight layout
        self.fig.tight_layout()
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, self.realtime_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill='both', expand=True, padx=5, pady=5)
        
        # Add toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.realtime_frame)
        self.toolbar.update()
        
    def create_analysis_tab(self):
        self.analysis_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.analysis_frame, text="Analysis Results")
        
        # Results display
        results_frame = ttk.LabelFrame(self.analysis_frame, text="Calculated Properties", padding="10")
        results_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create results table
        columns = ('Property', 'Value', 'Unit')
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=150)
        
        self.results_tree.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Scrollbar for results
        results_scrollbar = ttk.Scrollbar(results_frame, orient='vertical', command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=results_scrollbar.set)
        results_scrollbar.pack(side='right', fill='y')
        
        # Analysis buttons
        analysis_buttons_frame = ttk.Frame(results_frame)
        analysis_buttons_frame.pack(fill='x', pady=10)
        
        ttk.Button(analysis_buttons_frame, text="Calculate Properties", 
                  command=self.calculate_material_properties).pack(side='left', padx=5)
        ttk.Button(analysis_buttons_frame, text="Export Results", 
                  command=self.export_analysis_results).pack(side='left', padx=5)
        ttk.Button(analysis_buttons_frame, text="Generate Report", 
                  command=self.generate_test_report).pack(side='left', padx=5)
        
    def create_properties_tab(self):
        self.properties_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.properties_frame, text="Material Database")
        
        # Material database
        db_frame = ttk.LabelFrame(self.properties_frame, text="Material Properties Database", padding="10")
        db_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create material properties table
        prop_columns = ('Material', 'Young\'s Modulus (GPa)', 'Yield Strength (MPa)', 'Ultimate Strength (MPa)')
        self.props_tree = ttk.Treeview(db_frame, columns=prop_columns, show='headings', height=15)
        
        for col in prop_columns:
            self.props_tree.heading(col, text=col)
            self.props_tree.column(col, width=150)
        
        self.props_tree.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Add sample material data
        self.populate_material_database()
        
    def populate_material_database(self):
        materials = [
            ("Steel (Low Carbon)", "200", "250", "400"),
            ("Steel (High Carbon)", "200", "380", "600"),
            ("Aluminum 6061-T6", "69", "275", "310"),
            ("Aluminum 2024-T4", "73", "325", "470"),
            ("Copper", "120", "70", "220"),
            ("Brass", "100", "200", "400"),
            ("Titanium Ti-6Al-4V", "114", "880", "950"),
            ("Stainless Steel 304", "200", "205", "515"),
            ("ABS Plastic", "2.3", "40", "40"),
            ("Nylon 6", "3.0", "50", "80"),
            ("PTFE", "0.5", "23", "27"),
            ("Carbon Fiber", "150", "3500", "3500"),
            ("Glass Fiber", "73", "3400", "3400")
        ]
        
        for material in materials:
            self.props_tree.insert('', 'end', values=material)
        
    def start_plotting(self):
        if not self.is_plotting:
            self.is_plotting = True
            self.start_plot_btn.config(state='disabled')
            self.stop_plot_btn.config(state='normal')
            
            # Update test parameters
            self.specimen_area = self.area_var.get()
            self.gauge_length = self.gauge_var.get()
            self.material_type = self.material_var.get()
            self.test_mode = self.test_mode_var.get()
            
            # Start plotting thread
            self.plot_update_thread = threading.Thread(target=self._plot_update_loop, daemon=True)
            self.plot_update_thread.start()
            
            logging.info(f"Started plotting for {self.material_type} {self.test_mode} test")
        
    def stop_plotting(self):
        if self.is_plotting:
            self.is_plotting = False
            self.start_plot_btn.config(state='normal')
            self.stop_plot_btn.config(state='disabled')
            logging.info("Stopped plotting")
        
    def clear_plot_data(self):
        """Clear all plot data"""
        self.time_data.clear()
        self.load_data.clear()
        self.position_data.clear()
        self.stress_data.clear()
        self.strain_data.clear()
        self.displacement_data.clear()
        
        # Clear plots
        self.line1.set_data([], [])
        self.line2.set_data([], [])
        self.line3.set_data([], [])
        self.line4.set_data([], [])
        
        # Clear axes
        for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
            ax.relim()
            ax.autoscale_view()
        
        self.canvas.draw()
        logging.info("Cleared plot data")
        
    def _plot_update_loop(self):
        """Background thread for updating plots"""
        start_time = time.time()
        
        while self.is_plotting:
            try:
                # Get current data from controller
                current_time = time.time() - start_time
                load = self.controller.load_value
                position = self.controller.position_value
                
                # Add data points
                self.time_data.append(current_time)
                self.load_data.append(load)
                self.position_data.append(position)
                
                # Calculate stress and strain
                stress = load / self.specimen_area if self.specimen_area > 0 else 0  # MPa
                strain = (position / self.gauge_length) * 100 if self.gauge_length > 0 else 0  # %
                displacement = position
                
                self.stress_data.append(stress)
                self.strain_data.append(strain)
                self.displacement_data.append(displacement)
                
                # Limit data points
                max_points = self.config.MAX_PLOT_POINTS
                if len(self.time_data) > max_points:
                    self.time_data = self.time_data[-max_points:]
                    self.load_data = self.load_data[-max_points:]
                    self.position_data = self.position_data[-max_points:]
                    self.stress_data = self.stress_data[-max_points:]
                    self.strain_data = self.strain_data[-max_points:]
                    self.displacement_data = self.displacement_data[-max_points:]
                
                # Update plots on main thread
                self.parent.after_idle(self._update_plots)
                
                # Wait for next update
                time.sleep(1.0 / self.config.PLOT_REFRESH_RATE)
                
            except Exception as e:
                logging.error(f"Error in plot update loop: {e}")
                break
        
    def _update_plots(self):
        try:
            if not self.time_data:
                return
            
            # Update plot data
            self.line1.set_data(self.time_data, self.load_data)
            self.line2.set_data(self.time_data, self.position_data)
            self.line3.set_data(self.strain_data, self.stress_data)
            self.line4.set_data(self.displacement_data, self.load_data)
            
            # Auto scale if enabled
            if self.auto_scale_var.get():
                for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
                    ax.relim()
                    ax.autoscale_view()
            
            # Redraw canvas
            self.canvas.draw_idle()
            
        except Exception as e:
            logging.error(f"Error updating plots: {e}")
    
    def calculate_material_properties(self):
        """Calculate material properties from test data"""
        try:
            if len(self.stress_data) < 10 or len(self.strain_data) < 10:
                messagebox.showwarning("Insufficient Data", "Not enough data points for analysis")
                return
            
            # Convert to numpy arrays
            stress = np.array(self.stress_data)
            strain = np.array(self.strain_data)
            
            # Remove any invalid data
            valid_indices = ~(np.isnan(stress) | np.isnan(strain) | np.isinf(stress) | np.isinf(strain))
            stress = stress[valid_indices]
            strain = strain[valid_indices]
            
            if len(stress) < 5:
                messagebox.showwarning("Invalid Data", "Not enough valid data points for analysis")
                return
            
            # Calculate Young's modulus (linear region - first 20% of data)
            linear_end = int(len(stress) * 0.2)
            if linear_end < 5:
                linear_end = min(len(stress), 5)
            
            linear_stress = stress[:linear_end]
            linear_strain = strain[:linear_end]
            
            if len(linear_stress) >= 2:
                slope, intercept, r_value, p_value, std_err = stats.linregress(linear_strain, linear_stress)
                self.youngs_modulus = slope * 1000  # Convert to GPa
            else:
                self.youngs_modulus = 0
            
            # Calculate yield strength (0.2% offset method)
            offset_strain = strain + 0.2
            offset_stress = self.youngs_modulus * offset_strain / 1000  # Convert back to MPa
            
            # Find intersection
            diff = stress - offset_stress
            yield_index = np.where(diff > 0)[0]
            if len(yield_index) > 0:
                self.yield_strength = stress[yield_index[0]]
            else:
                self.yield_strength = 0
            
            # Ultimate strength (maximum stress)
            self.ultimate_strength = np.max(stress)
            
            # Fracture strength (final stress before failure)
            self.fracture_strength = stress[-1]
            
            # Elongation at break
            self.elongation_at_break = strain[-1]
            
            # Update results display
            self.update_results_display()
            
            logging.info("Material properties calculated successfully")
            
        except Exception as e:
            logging.error(f"Error calculating material properties: {e}")
            messagebox.showerror("Calculation Error", f"Error calculating properties: {e}")
    
    def update_results_display(self):
        # Clear existing results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # Add calculated results
        results = [
            ("Young's Modulus", f"{self.youngs_modulus:.2f}", "GPa"),
            ("Yield Strength", f"{self.yield_strength:.2f}", "MPa"),
            ("Ultimate Strength", f"{self.ultimate_strength:.2f}", "MPa"),
            ("Fracture Strength", f"{self.fracture_strength:.2f}", "MPa"),
            ("Elongation at Break", f"{self.elongation_at_break:.2f}", "%"),
            ("Material Type", self.material_type, "-"),
            ("Test Mode", self.test_mode, "-"),
            ("Cross-sectional Area", f"{self.specimen_area:.2f}", "mm²"),
            ("Gauge Length", f"{self.gauge_length:.2f}", "mm"),
            ("Data Points", str(len(self.stress_data)), "-")
        ]
        
        for result in results:
            self.results_tree.insert('', 'end', values=result)
    
    def export_analysis_results(self):
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Export Analysis Results"
            )
            
            if filename:
                with open(filename, 'w', newline='') as file:
                    file.write("UTM Test Analysis Results\n")
                    file.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    file.write(f"Material: {self.material_type}\n")
                    file.write(f"Test Mode: {self.test_mode}\n\n")
                    
                    file.write("Property,Value,Unit\n")
                    file.write(f"Young's Modulus,{self.youngs_modulus:.2f},GPa\n")
                    file.write(f"Yield Strength,{self.yield_strength:.2f},MPa\n")
                    file.write(f"Ultimate Strength,{self.ultimate_strength:.2f},MPa\n")
                    file.write(f"Fracture Strength,{self.fracture_strength:.2f},MPa\n")
                    file.write(f"Elongation at Break,{self.elongation_at_break:.2f},%\n\n")
                    
                    file.write("Raw Data\n")
                    file.write("Time (s),Load (N),Position (mm),Stress (MPa),Strain (%)\n")
                    
                    for i in range(len(self.time_data)):
                        file.write(f"{self.time_data[i]:.3f},{self.load_data[i]:.2f},"
                                 f"{self.position_data[i]:.3f},{self.stress_data[i]:.2f},"
                                 f"{self.strain_data[i]:.3f}\n")
                
                messagebox.showinfo("Export Successful", f"Results exported to {filename}")
                logging.info(f"Analysis results exported to {filename}")
                
        except Exception as e:
            logging.error(f"Error exporting results: {e}")
            messagebox.showerror("Export Error", f"Error exporting results: {e}")
    
    def generate_test_report(self):
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Generate Test Report"
            )
            
            if filename:
                with open(filename, 'w') as file:
                    file.write("="*80 + "\n")
                    file.write("UNIVERSAL TESTING MACHINE - TEST REPORT\n")
                    file.write("="*80 + "\n\n")
                    
                    file.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    file.write(f"Material: {self.material_type}\n")
                    file.write(f"Test Type: {self.test_mode}\n")
                    file.write(f"Specimen Cross-sectional Area: {self.specimen_area:.2f} mm²\n")
                    file.write(f"Gauge Length: {self.gauge_length:.2f} mm\n\n")
                    
                    file.write("MECHANICAL PROPERTIES:\n")
                    file.write("-"*40 + "\n")
                    file.write(f"Young's Modulus (E): {self.youngs_modulus:.2f} GPa\n")
                    file.write(f"Yield Strength (σy): {self.yield_strength:.2f} MPa\n")
                    file.write(f"Ultimate Tensile Strength (σu): {self.ultimate_strength:.2f} MPa\n")
                    file.write(f"Fracture Strength (σf): {self.fracture_strength:.2f} MPa\n")
                    file.write(f"Elongation at Break: {self.elongation_at_break:.2f} %\n\n")
                    
                    # Add statistical summary
                    if len(self.stress_data) > 0:
                        file.write("STATISTICAL SUMMARY:\n")
                        file.write("-"*40 + "\n")
                        file.write(f"Maximum Load: {max(self.load_data):.2f} N\n")
                        file.write(f"Maximum Displacement: {max(self.position_data):.3f} mm\n")
                        file.write(f"Total Test Time: {max(self.time_data):.1f} seconds\n")
                        file.write(f"Data Points Collected: {len(self.time_data)}\n\n")
                    
                    file.write("TEST NOTES:\n")
                    file.write("-"*40 + "\n")
                    file.write("This report was generated automatically by UTM Controller.\n")
                    file.write("Please verify all values and add any additional observations.\n")
                
                messagebox.showinfo("Report Generated", f"Test report saved to {filename}")
                logging.info(f"Test report generated: {filename}")
                
        except Exception as e:
            logging.error(f"Error generating report: {e}")
            messagebox.showerror("Report Error", f"Error generating report: {e}")
    
    def add_data_point(self, timestamp, load, position):
        """Add a data point from external source"""
        if self.is_plotting:
            # This method allows external components to add data
            current_time = timestamp
            self.time_data.append(current_time)
            self.load_data.append(load)
            self.position_data.append(position)
            
            # Calculate derived values
            stress = load / self.specimen_area if self.specimen_area > 0 else 0
            strain = (position / self.gauge_length) * 100 if self.gauge_length > 0 else 0
            
            self.stress_data.append(stress)
            self.strain_data.append(strain)
            self.displacement_data.append(position)
