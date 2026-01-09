class UTMConfig:
    # Serial communication settings
    DEFAULT_BAUDRATE = 9600
    SERIAL_TIMEOUT = 1
    RECONNECT_ATTEMPTS = 3
    RECONNECT_DELAY = 2
    
    # GUI settings
    WINDOW_TITLE = "UTM Controller - Universal Testing Machine"
    WINDOW_SIZE = "800x600"
    WINDOW_MIN_SIZE = (600, 400)
    
    # Update rates (Hz)
    SERIAL_READ_RATE = 10  # 10 Hz
    GUI_UPDATE_RATE = 5    # 5 Hz
    
    # Command codes for Arduino communication
    COMMANDS = {
        'TURBOSET': 'T',
        'OPEN': '1',
        'CLOSE': '2',
        'STOP': '0',
        'ZERO': 'Z',
        'TEST': 'TEST',
        'SET_SPEED': 'S',
        'GET_SPEED': 'G'
    }
    
    # PCB button mapping
    PCB_BUTTONS = {
        '1': 'OPEN',
        '2': 'CLOSE',
        '3': 'STOP',
        '4': 'ZERO'
    }
    
    # Data processing settings
    DATA_BUFFER_SIZE = 1000
    MAX_LOG_ENTRIES = 10000
    
    # File paths
    LOG_FILE = "utm_controller.log"
    DATA_EXPORT_DIR = "exported_data"
    
    # Safety limits (customize based on your UTM)
    MAX_LOAD = 10000  # N
    MAX_POSITION = 100  # mm
    MIN_POSITION = -5   # mm
    
    # Stepper motor speed settings
    MIN_SPEED = 1      # RPM
    MAX_SPEED = 200    # RPM
    DEFAULT_SPEED = 10 # RPM
    
    # Material testing parameters
    MATERIAL_TYPES = ['Steel', 'Aluminum', 'Plastic', 'Composite', 'Rubber', 'Custom']
    
    # Graph plotting settings
    PLOT_REFRESH_RATE = 2  # Hz
    MAX_PLOT_POINTS = 1000
    
    # Testing modes
    TEST_MODES = {
        'TENSILE': 'Tensile Test',
        'COMPRESSION': 'Compression Test',
        'CYCLIC': 'Cyclic Test',
        'CREEP': 'Creep Test'
    }
    
    # Color scheme
    COLORS = {
        'connected': 'green',
        'disconnected': 'red',
        'running': 'blue',
        'stopped': 'orange',
        'error': 'red',
        'warning': 'orange'
    }
    
    # Font settings
    FONTS = {
        'default': ('Arial', 10),
        'bold': ('Arial', 10, 'bold'),
        'large': ('Arial', 12),
        'large_bold': ('Arial', 12, 'bold'),
        'display': ('Arial', 16, 'bold')
    }
    
    def __init__(self):
        """Initialize configuration"""
        self.load_user_settings()
    
    def load_user_settings(self):
        """Load user-specific settings (placeholder for future implementation)"""
        # This could load from a config file, registry, or database
        pass
    
    def save_user_settings(self):
        """Save user-specific settings (placeholder for future implementation)"""
        # This could save to a config file, registry, or database
        pass
    
    @classmethod
    def get_command_code(cls, command_name):
        """Get command code for given command name"""
        return cls.COMMANDS.get(command_name.upper(), None)
    
    @classmethod
    def get_pcb_button_name(cls, button_code):
        """Get button name for given PCB button code"""
        return cls.PCB_BUTTONS.get(button_code, None)
