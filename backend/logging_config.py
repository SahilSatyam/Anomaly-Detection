"""
Structured Logging Configuration

Provides JSON-formatted structured logging for production environments.
Supports both human-readable and JSON formats based on environment.
"""

import os
import sys
import json
import logging
import traceback
from datetime import datetime
from typing import Optional, Dict, Any
from functools import wraps
import time


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    
    Output format:
    {
        "timestamp": "2024-01-15T10:30:00.000Z",
        "level": "INFO",
        "logger": "module.name",
        "message": "Log message",
        "extra": {...}
    }
    """
    
    def __init__(self, include_traceback: bool = True):
        super().__init__()
        self.include_traceback = include_traceback
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add process/thread info for debugging
        log_data["process"] = {
            "id": record.process,
            "name": record.processName,
        }
        log_data["thread"] = {
            "id": record.thread,
            "name": record.threadName,
        }
        
        # Add exception info if present
        if record.exc_info and self.include_traceback:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info) if record.exc_info[0] else None,
            }
        
        # Add any extra fields from the record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'created', 'filename', 'funcName',
                'levelname', 'levelno', 'lineno', 'module', 'msecs',
                'pathname', 'process', 'processName', 'relativeCreated',
                'stack_info', 'exc_info', 'exc_text', 'thread', 'threadName',
                'message', 'asctime'
            }:
                try:
                    # Try to serialize the value
                    json.dumps(value)
                    extra_fields[key] = value
                except (TypeError, ValueError):
                    extra_fields[key] = str(value)
        
        if extra_fields:
            log_data["extra"] = extra_fields
        
        return json.dumps(log_data, default=str)


class ColoredFormatter(logging.Formatter):
    """
    Colored formatter for development environment.
    """
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[41m', # Red background
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging(
    level: str = None,
    format_type: str = None,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Setup structured logging for the application.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: 'json' for structured logging, 'text' for human-readable
        log_file: Optional file path for log output
        
    Returns:
        Configured root logger
    """
    # Get configuration from environment or use defaults
    level = level or os.getenv('LOG_LEVEL', 'INFO')
    format_type = format_type or os.getenv('LOG_FORMAT', 'text')
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Clear existing handlers
    root_logger.handlers = []
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(root_logger.level)
    
    # Set formatter based on format type
    if format_type.lower() == 'json':
        formatter = JSONFormatter()
    else:
        # Development format with colors
        fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

        if os.getenv('ENV') == 'development':
            # Add process/thread info for debugging
            fmt = '%(asctime)s - %(name)s - [%(process)d:%(thread)d] - %(levelname)s - %(message)s'

        if sys.stdout.isatty():
            formatter = ColoredFormatter(fmt, datefmt='%Y-%m-%d %H:%M:%S')
        else:
            formatter = logging.Formatter(fmt, datefmt='%Y-%m-%d %H:%M:%S')
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(root_logger.level)
        file_handler.setFormatter(JSONFormatter())  # Always JSON for files
        root_logger.addHandler(file_handler)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the given name.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class LogContext:
    """
    Context manager for adding extra fields to log records.
    
    Usage:
        with LogContext(request_id="123", user_id="456"):
            logger.info("Processing request")
    """
    
    _context: Dict[str, Any] = {}
    
    def __init__(self, **kwargs):
        self.fields = kwargs
        self.old_factory = None
    
    def __enter__(self):
        LogContext._context.update(self.fields)
        
        # Create custom record factory that adds context
        old_factory = logging.getLogRecordFactory()
        self.old_factory = old_factory
        
        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            for key, value in LogContext._context.items():
                setattr(record, key, value)
            return record
        
        logging.setLogRecordFactory(record_factory)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        for key in self.fields:
            LogContext._context.pop(key, None)
        
        if self.old_factory:
            logging.setLogRecordFactory(self.old_factory)


def log_execution_time(logger: logging.Logger = None, level: int = logging.DEBUG):
    """
    Decorator to log function execution time.
    
    Usage:
        @log_execution_time()
        def my_function():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = logging.getLogger(func.__module__)
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.log(
                    level,
                    f"{func.__name__} completed in {duration:.3f}s",
                    extra={'duration_seconds': duration, 'function': func.__name__}
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"{func.__name__} failed after {duration:.3f}s: {e}",
                    extra={'duration_seconds': duration, 'function': func.__name__},
                    exc_info=True
                )
                raise
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = logging.getLogger(func.__module__)
            
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                logger.log(
                    level,
                    f"{func.__name__} completed in {duration:.3f}s",
                    extra={'duration_seconds': duration, 'function': func.__name__}
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"{func.__name__} failed after {duration:.3f}s: {e}",
                    extra={'duration_seconds': duration, 'function': func.__name__},
                    exc_info=True
                )
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    
    return decorator


# Initialize logging on module import
if os.getenv('LOG_FORMAT') == 'json':
    setup_logging()
