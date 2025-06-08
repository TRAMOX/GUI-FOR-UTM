"""
Utility functions for the UTM Controller application
Helper functions for common tasks
"""

import serial.tools.list_ports
import logging
import os
import time
import csv
from datetime import datetime
import threading

def get_available_ports():
    """Get list of available serial ports with detailed information"""
    try:
        ports = []
        for port_info in serial.tools.list_ports.comports():
            port_data = {
                'device': port_info.device,
                'description': port_info.description,
                'hwid': port_info.hwid,
                'vid': getattr(port_info, 'vid', None),
                'pid': getattr(port_info, 'pid', None),
                'serial_number': getattr(port_info, 'serial_number', None),
                'manufacturer': getattr(port_info, 'manufacturer', None)
            }
            ports.append(port_data)
        
        logging.debug(f"Found {len(ports)} available ports")
        return ports
        
    except Exception as e:
        logging.error(f"Error getting available ports: {e}")
        return []

def filter_arduino_ports(ports):
    """Filter ports to show likely Arduino devices"""
    arduino_keywords = [
        'arduino', 'ch340', 'ch341', 'cp210', 'ftdi', 'prolific',
        'usb serial', 'usb-serial', 'silicon labs'
    ]
    
    filtered_ports = []
    for port in ports:
        description_lower = port['description'].lower()
        if any(keyword in description_lower for keyword in arduino_keywords):
            filtered_ports.append(port)
    
    return filtered_ports if filtered_ports else ports

def validate_numeric_input(value, min_val=None, max_val=None):
    """Validate numeric input within specified range"""
    try:
        num_val = float(value)
        
        if min_val is not None and num_val < min_val:
            return False, f"Value must be >= {min_val}"
        
        if max_val is not None and num_val > max_val:
            return False, f"Value must be <= {max_val}"
        
        return True, num_val
        
    except ValueError:
        return False, "Invalid numeric value"

def format_timestamp(timestamp=None):
    """Format timestamp for display"""
    if timestamp is None:
        timestamp = time.time()
    
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

def create_data_export_filename(prefix="utm_data", extension="csv"):
    """Create filename for data export with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.{extension}"

def ensure_directory_exists(directory_path):
    """Ensure directory exists, create if necessary"""
    try:
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
            logging.info(f"Created directory: {directory_path}")
        return True
    except Exception as e:
        logging.error(f"Error creating directory {directory_path}: {e}")
        return False

class DataLogger:
    """Data logging utility class"""
    
    def __init__(self, filename=None, max_entries=10000):
        self.filename = filename or create_data_export_filename()
        self.max_entries = max_entries
        self.data_buffer = []
        self.lock = threading.Lock()
        self.logging_active = False
        
    def start_logging(self):
        """Start data logging"""
        with self.lock:
            self.logging_active = True
            self.data_buffer = []
        logging.info(f"Data logging started: {self.filename}")
    
    def stop_logging(self):
        """Stop data logging"""
        with self.lock:
            self.logging_active = False
        logging.info("Data logging stopped")
    
    def log_data_point(self, timestamp, load, position, state):
        """Log a single data point"""
        if not self.logging_active:
            return
        
        with self.lock:
            data_point = {
                'timestamp': timestamp,
                'load': load,
                'position': position,
                'state': state
            }
            
            self.data_buffer.append(data_point)
            
            # Limit buffer size
            if len(self.data_buffer) > self.max_entries:
                self.data_buffer.pop(0)
    
    def export_to_csv(self, filename=None):
        """Export logged data to CSV file"""
        try:
            export_filename = filename or self.filename
            
            with self.lock:
                if not self.data_buffer:
                    logging.warning("No data to export")
                    return False
                
                with open(export_filename, 'w', newline='') as csvfile:
                    fieldnames = ['timestamp', 'load', 'position', 'state']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    writer.writeheader()
                    for data_point in self.data_buffer:
                        writer.writerow(data_point)
                
                logging.info(f"Data exported to: {export_filename}")
                return True
                
        except Exception as e:
            logging.error(f"Error exporting data: {e}")
            return False
    
    def get_statistics(self):
        """Get statistics about logged data"""
        with self.lock:
            if not self.data_buffer:
                return {
                    'count': 0,
                    'max_load': 0,
                    'min_load': 0,
                    'avg_load': 0,
                    'max_position': 0,
                    'min_position': 0,
                    'duration': 0
                }
            
            loads = [point['load'] for point in self.data_buffer]
            positions = [point['position'] for point in self.data_buffer]
            timestamps = [point['timestamp'] for point in self.data_buffer]
            
            return {
                'count': len(self.data_buffer),
                'max_load': max(loads),
                'min_load': min(loads),
                'avg_load': sum(loads) / len(loads),
                'max_position': max(positions),
                'min_position': min(positions),
                'duration': max(timestamps) - min(timestamps) if len(timestamps) > 1 else 0
            }

class SafetyMonitor:
    """Safety monitoring utility class"""
    
    def __init__(self, max_load=10000, max_position=100, min_position=-5):
        self.max_load = max_load
        self.max_position = max_position
        self.min_position = min_position
        self.safety_callbacks = []
    
    def add_safety_callback(self, callback):
        """Add callback for safety violations"""
        self.safety_callbacks.append(callback)
    
    def check_safety_limits(self, load, position):
        """Check if current values exceed safety limits"""
        violations = []
        
        if abs(load) > self.max_load:
            violations.append(f"Load exceeded maximum: {load} > {self.max_load}")
        
        if position > self.max_position:
            violations.append(f"Position exceeded maximum: {position} > {self.max_position}")
        
        if position < self.min_position:
            violations.append(f"Position below minimum: {position} < {self.min_position}")
        
        if violations:
            for callback in self.safety_callbacks:
                try:
                    callback(violations)
                except Exception as e:
                    logging.error(f"Error in safety callback: {e}")
        
        return len(violations) == 0

def debounce_function(wait_time):
    """Decorator to debounce function calls"""
    def decorator(func):
        last_called = [0]
        
        def wrapper(*args, **kwargs):
            current_time = time.time()
            if current_time - last_called[0] >= wait_time:
                last_called[0] = current_time
                return func(*args, **kwargs)
        
        return wrapper
    return decorator

def retry_on_exception(max_attempts=3, delay=1):
    """Decorator to retry function on exception"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    logging.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
        return wrapper
    return decorator
