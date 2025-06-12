"""
Log Utils - Compatible Version
"""
import logging
import logging.handlers
import os
import structlog
from typing import Optional, Any
from configs.settings import settings

class CustomLogger:
    """Custom Logger class, supports error parameters and structlog style"""
    
    def __init__(self, name: str = None):
        self._logger = logging.getLogger(name or __name__)
        self._struct_logger = structlog.get_logger(name or __name__)
        
        # Ensure logger level is set correctly
        log_level = getattr(logging, settings.log_level.upper(), logging.DEBUG)
        self._logger.setLevel(log_level)
    
    def _format_message_with_kwargs(self, message: str, **kwargs) -> str:
        """Format kwargs into message"""
        if kwargs:
            kwargs_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
            return f"{message} [{kwargs_str}]"
        return message
    
    def debug(self, message: str, error: Optional[Any] = None, **kwargs):
        """Debug log"""
        if error:
            formatted_msg = self._format_message_with_kwargs(f"{message}: {error}", **kwargs)
            self._logger.debug(formatted_msg)
            self._struct_logger.debug(message, error=str(error), **kwargs)
        else:
            formatted_msg = self._format_message_with_kwargs(message, **kwargs)
            self._logger.debug(formatted_msg)
            self._struct_logger.debug(message, **kwargs)
    
    def info(self, message: str, error: Optional[Any] = None, **kwargs):
        """Info log - Compatible with structlog style"""
        if error:
            formatted_msg = self._format_message_with_kwargs(f"{message}: {error}", **kwargs)
            self._logger.info(formatted_msg)
            self._struct_logger.info(message, error=str(error), **kwargs)
        elif kwargs:
            # If there are other parameters, use structlog style
            self._struct_logger.info(message, **kwargs)
            # Also record with standard logger (without passing kwargs)
            formatted_msg = self._format_message_with_kwargs(message, **kwargs)
            self._logger.info(formatted_msg)
        else:
            self._logger.info(message)
            self._struct_logger.info(message)
    
    def warning(self, message: str, error: Optional[Any] = None, **kwargs):
        """Warning log"""
        if error:
            formatted_msg = self._format_message_with_kwargs(f"{message}: {error}", **kwargs)
            self._logger.warning(formatted_msg)
            self._struct_logger.warning(message, error=str(error), **kwargs)
        elif kwargs:
            self._struct_logger.warning(message, **kwargs)
            formatted_msg = self._format_message_with_kwargs(message, **kwargs)
            self._logger.warning(formatted_msg)
        else:
            self._logger.warning(message)
            self._struct_logger.warning(message)
    
    def error(self, message: str, error: Optional[Any] = None, **kwargs):
        """Error log"""
        if error:
            formatted_msg = self._format_message_with_kwargs(f"{message}: {error}", **kwargs)
            self._logger.error(formatted_msg, exc_info=True)
            self._struct_logger.error(message, error=str(error), **kwargs)
        elif kwargs:
            self._struct_logger.error(message, **kwargs)
            formatted_msg = self._format_message_with_kwargs(message, **kwargs)
            self._logger.error(formatted_msg)
        else:
            self._logger.error(message)
            self._struct_logger.error(message)
    
    def critical(self, message: str, error: Optional[Any] = None, **kwargs):
        """Critical error log"""
        if error:
            formatted_msg = self._format_message_with_kwargs(f"{message}: {error}", **kwargs)
            self._logger.critical(formatted_msg, exc_info=True)
            self._struct_logger.critical(message, error=str(error), **kwargs)
        elif kwargs:
            self._struct_logger.critical(message, **kwargs)
            formatted_msg = self._format_message_with_kwargs(message, **kwargs)
            self._logger.critical(formatted_msg)
        else:
            self._logger.critical(message)
            self._struct_logger.critical(message)
    
    def exception(self, message: str, **kwargs):
        """Exception log (automatically includes stack information)"""
        formatted_msg = self._format_message_with_kwargs(message, **kwargs)
        self._logger.exception(formatted_msg)
        self._struct_logger.exception(message, **kwargs)

def setup_logging():
    """Setup logging configuration"""
    # Ensure log directory exists
    if settings.log_file:
        log_dir = os.path.dirname(settings.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
    
    # Get log level
    log_level = getattr(logging, settings.log_level.upper(), logging.DEBUG)
    
    # Create handlers list
    handlers = []
    
    # File handler
    if settings.log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            settings.log_file,
            maxBytes=settings.log_max_size,
            backupCount=settings.log_backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        handlers.append(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    handlers.append(console_handler)
    
    # Configure standard logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers,
        force=True  # Force reconfiguration
    )
    
    # Set root logger level
    logging.getLogger().setLevel(log_level)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Verify logging configuration
    test_logger = logging.getLogger("setup_test")
    test_logger.debug("Debug logging is enabled")
    test_logger.info(f"Logging setup completed - Level: {settings.log_level}")
    
    print(f"=== Logging Configuration Info ===")
    print(f"Log Level: {settings.log_level} ({log_level})")
    print(f"Log File: {settings.log_file}")
    print(f"Root Logger Level: {logging.getLogger().level}")
    print(f"Number of Handlers: {len(handlers)}")
    for i, handler in enumerate(handlers):
        print(f"  Handler {i}: {type(handler).__name__} - Level: {handler.level}")

def get_logger(name: str = None) -> CustomLogger:
    """Get custom logger"""
    return CustomLogger(name)

# To maintain compatibility with existing code, also provide structlog getter
def get_struct_logger(name: str = None):
    """Get structlog logger"""
    return structlog.get_logger(name)

# Initialize logging
setup_logging()
