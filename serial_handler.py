import serial
import serial.tools.list_ports
import threading
import time
import logging
import queue

class SerialHandler:
    def __init__(self):
        self.connection = None
        self.connected = False
        self.port = None
        self.baudrate = 9600
        self.timeout = 1
        
        # Threading
        self.read_thread = None
        self.write_queue = queue.Queue()
        self.running = False
        
        # Callbacks
        self.data_callback = None
        self.connection_callback = None
        
        # Data buffers
        self.receive_buffer = ""
        
    def set_data_callback(self, callback):
        """Set callback function for received data"""
        self.data_callback = callback
    
    def set_connection_callback(self, callback):
        self.connection_callback = callback
    
    def get_available_ports(self):
        """Get list of available serial ports"""
        try:
            ports = []
            for port in serial.tools.list_ports.comports():
                ports.append({
                    'device': port.device,
                    'description': port.description,
                    'hwid': port.hwid
                })
            return ports
        except Exception as e:
            logging.error(f"Error getting available ports: {e}")
            return []
    
    def connect(self, port, baudrate=9600):
        try:
            if self.connected:
                self.disconnect()
            
            self.port = port
            self.baudrate = baudrate
            
            # Create serial connection
            self.connection = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=self.timeout,
                write_timeout=self.timeout
            )
            
            # Wait for Arduino to initialize
            time.sleep(2)
            
            # Test connection
            if self.connection.is_open:
                self.connected = True
                self.running = True
                
                # Start read thread
                self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
                self.read_thread.start()
                
                # Notify connection callback
                if self.connection_callback:
                    self.connection_callback(True)
                
                logging.info(f"Successfully connected to {port} at {baudrate} baud")
                return True
            else:
                raise Exception("Failed to open serial port")
                
        except Exception as e:
            logging.error(f"Error connecting to {port}: {e}")
            self.connected = False
            if self.connection_callback:
                self.connection_callback(False)
            return False
    
    def disconnect(self):
        """Disconnect from serial port"""
        try:
            self.running = False
            self.connected = False
            
            # Close connection
            if self.connection and self.connection.is_open:
                self.connection.close()
                self.connection = None
            
            # Wait for read thread to finish
            if self.read_thread and self.read_thread.is_alive():
                self.read_thread.join(timeout=2)
            
            # Notify connection callback
            if self.connection_callback:
                self.connection_callback(False)
            
            logging.info("Disconnected from serial port")
            
        except Exception as e:
            logging.error(f"Error disconnecting: {e}")
    
    def is_connected(self):
        """Check if serial connection is active"""
        return self.connected and self.connection and self.connection.is_open
    
    def send_command(self, command):
        """Send command to Arduino"""
        try:
            if not self.is_connected():
                raise Exception("Not connected to Arduino")
            
            # Format command with newline
            cmd_str = f"{command}\n"
            
            # Send command
            bytes_written = self.connection.write(cmd_str.encode('utf-8'))
            self.connection.flush()
            
            logging.debug(f"Sent command: {command} ({bytes_written} bytes)")
            return True
            
        except Exception as e:
            logging.error(f"Error sending command '{command}': {e}")
            # Try to reconnect if connection lost
            self._handle_connection_error()
            return False
    
    def read_data(self):
        """Read available data from Arduino (non-blocking)"""
        try:
            if not self.is_connected():
                return None
            
            if self.connection.in_waiting > 0:
                data = self.connection.readline().decode('utf-8').strip()
                if data:
                    logging.debug(f"Received: {data}")
                    return data
            
            return None
            
        except Exception as e:
            logging.error(f"Error reading data: {e}")
            self._handle_connection_error()
            return None
    
    def _read_loop(self):
        """Background thread for continuous data reading"""
        while self.running and self.connected:
            try:
                if self.connection and self.connection.is_open:
                    # Read data with timeout
                    if self.connection.in_waiting > 0:
                        line = self.connection.readline().decode('utf-8').strip()
                        if line:
                            # Process received data
                            self._process_received_data(line)
                else:
                    # Connection lost
                    self._handle_connection_error()
                    break
                
                time.sleep(0.01)  # Small delay to prevent CPU overload
                
            except serial.SerialException as e:
                logging.error(f"Serial exception in read loop: {e}")
                self._handle_connection_error()
                break
            except Exception as e:
                logging.error(f"Unexpected error in read loop: {e}")
                time.sleep(0.1)
    
    def _process_received_data(self, data):
        """Process received data and call callback"""
        try:
            # Add to buffer for line-based processing
            self.receive_buffer += data
            
            # Process complete lines
            while '\n' in self.receive_buffer:
                line, self.receive_buffer = self.receive_buffer.split('\n', 1)
                line = line.strip()
                
                if line and self.data_callback:
                    self.data_callback(line)
            
            # If no newline but we have data, process it anyway
            if data and self.data_callback:
                self.data_callback(data)
                
        except Exception as e:
            logging.error(f"Error processing received data: {e}")
    
    def _handle_connection_error(self):
        """Handle connection errors and attempt recovery"""
        try:
            logging.warning("Handling connection error")
            
            self.connected = False
            
            # Notify connection callback
            if self.connection_callback:
                self.connection_callback(False)
            
            # Try to close and reopen connection
            if self.connection:
                try:
                    self.connection.close()
                except:
                    pass
                self.connection = None
            
            # Attempt automatic reconnection after delay
            threading.Thread(target=self._attempt_reconnection, daemon=True).start()
            
        except Exception as e:
            logging.error(f"Error handling connection error: {e}")
    
    def _attempt_reconnection(self):
        """Attempt to reconnect to the last used port"""
        if not self.port:
            return
        
        max_attempts = 3
        attempt = 0
        
        while attempt < max_attempts and not self.connected:
            attempt += 1
            logging.info(f"Attempting reconnection {attempt}/{max_attempts}")
            
            time.sleep(2)  # Wait before retry
            
            try:
                if self.connect(self.port, self.baudrate):
                    logging.info("Automatic reconnection successful")
                    return
            except Exception as e:
                logging.error(f"Reconnection attempt {attempt} failed: {e}")
        
        logging.warning("Automatic reconnection failed after all attempts")
    
    def get_connection_info(self):
        """Get current connection information"""
        if self.is_connected():
            return {
                'port': self.port,
                'baudrate': self.baudrate,
                'connected': True,
                'in_waiting': self.connection.in_waiting if self.connection else 0
            }
        else:
            return {
                'port': self.port,
                'baudrate': self.baudrate,
                'connected': False,
                'in_waiting': 0
            }
    
    def flush_buffers(self):
        """Flush input and output buffers"""
        try:
            if self.is_connected():
                self.connection.reset_input_buffer()
                self.connection.reset_output_buffer()
                self.receive_buffer = ""
                logging.debug("Serial buffers flushed")
        except Exception as e:
            logging.error(f"Error flushing buffers: {e}")
