"""
Enhanced logging configuration for Resume Analyzer
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Optional

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
        return super().format(record)

def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    enable_console: bool = True,
    enable_colors: bool = True
) -> logging.Logger:
    """
    Setup comprehensive logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        enable_console: Whether to log to console
        enable_colors: Whether to use colored console output
    
    Returns:
        Configured logger instance
    """
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s | %(name)-20s | %(levelname)-8s | %(funcName)-15s:%(lineno)-3d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        if enable_colors and hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
            console_formatter = ColoredFormatter(
                fmt='%(asctime)s | %(name)-15s | %(levelname)-8s | %(message)s',
                datefmt='%H:%M:%S'
            )
        else:
            console_formatter = simple_formatter
            
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_file:
        # Use rotating file handler to prevent huge log files
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)
    
    # Error file handler (separate file for errors only)
    if log_file:
        error_file = log_file.replace('.log', '_errors.log')
        error_handler = logging.handlers.RotatingFileHandler(
            error_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(error_handler)
    
    # Add startup log entry
    logger = logging.getLogger('resume_analyzer.logger')
    logger.info(f"Logging initialized - Level: {log_level}, File: {log_file or 'None'}")
    
    return root_logger

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name"""
    return logging.getLogger(name)

class LogContext:
    """Context manager for adding context to log messages"""
    
    def __init__(self, logger: logging.Logger, context: str):
        self.logger = logger
        self.context = context
        self.original_name = logger.name
    
    def __enter__(self):
        self.logger.name = f"{self.original_name}[{self.context}]"
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.name = self.original_name
        if exc_type:
            self.logger.error(f"Exception in {self.context}: {exc_val}", exc_info=True)

def log_function_call(func):
    """Decorator to log function calls and exceptions"""
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        func_name = f"{func.__qualname__}"
        
        logger.debug(f"Calling {func_name}")
        start_time = datetime.now()
        
        try:
            result = func(*args, **kwargs)
            duration = (datetime.now() - start_time).total_seconds()
            logger.debug(f"Completed {func_name} in {duration:.3f}s")
            return result
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"Error in {func_name} after {duration:.3f}s: {str(e)}", exc_info=True)
            raise
    
    return wrapper