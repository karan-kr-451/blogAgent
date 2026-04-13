"""Logging configuration for the Autonomous Blog Agent."""

import logging
import sys
import json
from datetime import datetime
from typing import Any
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields from record
        if hasattr(record, "correlation_id"):
            log_data["correlation_id"] = record.correlation_id
        
        if hasattr(record, "agent"):
            log_data["agent"] = record.agent
        
        if hasattr(record, "url"):
            log_data["url"] = record.url
        
        # Filter out sensitive data patterns
        log_data = self._filter_sensitive_data(log_data)
        
        return json.dumps(log_data)
    
    def _filter_sensitive_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Remove or mask sensitive data from logs."""
        sensitive_keys = ["api_key", "token", "password", "secret", "authorization"]
        
        for key, value in data.items():
            if isinstance(value, str):
                # Check if key contains sensitive terms
                if any(sensitive in key.lower() for sensitive in sensitive_keys):
                    data[key] = "***REDACTED***"
                # Check if value looks like an API key (common patterns)
                elif self._looks_like_api_key(value):
                    data[key] = "***REDACTED***"
        
        return data
    
    def _looks_like_api_key(self, value: str) -> bool:
        """Check if string looks like an API key."""
        # Common API key patterns
        if len(value) > 20 and any(c.isalnum() for c in value):
            # Check for common prefixes
            if any(value.startswith(prefix) for prefix in ["sk-", "pk-", "Bearer ", "token_"]):
                return True
            # Check for long alphanumeric strings
            if len(value) > 32 and value.replace("-", "").replace("_", "").isalnum():
                return True
        return False


class TextFormatter(logging.Formatter):
    """Human-readable text formatter."""
    
    def __init__(self) -> None:
        super().__init__(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )


def setup_logging(log_level: str = "INFO", log_format: str = "json", log_file: str | None = None) -> None:
    """
    Configure logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Output format ("json" or "text")
        log_file: Optional file path for log output
    """
    # Create logs directory if needed
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Select formatter
    if log_format == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Set levels for noisy third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("playwright").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
