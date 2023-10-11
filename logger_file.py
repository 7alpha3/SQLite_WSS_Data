import logging
from logging.handlers import TimedRotatingFileHandler

class CustomLogger:
    
    def __init__(self, name=None, clear_log=False, level=logging.NOTSET):
        
        self.file_path = './debug/debug.txt'
        
        if clear_log:
            # Clear the log file when starting the application
            with open(self.file_path, 'w'):
                pass
        else:
            with open(self.file_path, 'a'):
                pass
        
        # Create a logger
        self.logger = logging.getLogger(name)
        
        self.logger.setLevel(level)

        # Create a timed rotating file handler
        self.handler = TimedRotatingFileHandler(filename=self.file_path, when='midnight', interval=1, backupCount=5, encoding='utf-8')

        # Create a formatter and set it for the handler
        format_str = "%(asctime)s | %(name)s | %(levelname)s | %(module)s | %(funcName)s | %(message)s"
        self.formatter = logging.Formatter(format_str)
        self.handler.setFormatter(self.formatter)

        # Set the logging level for the handler to DEBUG as well
        self.handler.setLevel(level)
        # Add the handler to the logger
        self.logger.addHandler(self.handler)
        
    def log(self, message, level=logging.DEBUG):
        # Log a message with the specified log level
        self.logger.log(level, message)

    def debug(self, message):
        # Log a message with DEBUG level
        self.log(message, logging.DEBUG)

    def info(self, message):
        # Log a message with INFO level
        self.log(message, logging.INFO)

    def warning(self, message):
        # Log a message with WARNING level
        self.log(message, logging.WARNING)

    def error(self, message):
        # Log a message with ERROR level
        self.log(message, logging.ERROR)

    def critical(self, message):
        # Log a message with CRITICAL level
        self.log(message, logging.CRITICAL)

    def close(self, message='Closing logger.'):
        # Close the logger when you're done
        self.log(message, logging.DEBUG)
        self.handler.close()

########## unused and archived code ##########

'''
self.CRITICAL = 50
self.ERROR = 40
self.WARNING = 30
self.INFO = 20
self.DEBUG = 10
self.NOTSET = 0 
'''

'''
# Example usage:
if __name__ == '__main__':
    custom_logger = CustomLogger(clear=True)
    custom_logger.debug("Debug message")
    custom_logger.info("Info message")
    custom_logger.warning("Warning message")
    custom_logger.error("Error message")
'''

'''# custom logging
def create_logger(clear=False, level=logging.DEBUG):
    
    file_path = 'debug/debug.txt'
    
    if clear:
        # clear the log file when starting application
        with open(file_path, 'w'):
            pass
    else:
        with open(file_path, 'a'):
            pass
            
    # Create a logger
    logger = logging.getLogger()
    logger.setLevel(level)

    # Create a timed rotating file handler
    handler = TimedRotatingFileHandler(filename=file_path, when='midnight', interval=1, backupCount=5)

    # Create a formatter and set it for the handler
    format_str = "%(asctime)s | %(name)s | %(levelname)s | %(module)s | %(funcName)s | %(message)s"
    formatter = logging.Formatter(format_str)
    handler.setFormatter(formatter)

    # Set the logging level for the handler to DEBUG as well
    handler.setLevel(level)
    # Add the handler to the logger
    logger.addHandler(handler)
    
    return logger

# basic logging
def setup_debug_logging(clear=False): 
    
    file_path = 'debug/basic_debug.txt'
    
    if clear:
        # clear the log file
        with open(file_path, 'w'):
            pass
    else:
        # clear the log file
        with open(file_path, 'a'):
            pass
        
    
    # Configure logging to write to a log file
    logging.basicConfig(
        filename=file_path,
        level=logging.DEBUG,
        format='%(asctime)s | %(name)s | %(levelname)s | %(module)s | %(funcName)s | %(message)s'
    )
    logging.debug('*** This is a debug test message! ***')
'''