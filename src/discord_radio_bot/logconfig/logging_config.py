import os
import sys
import logging
import structlog

def configure_logging() -> None:
    """Configure structlog based on environment variables.
    
    Environment variables:
    - LOGGING_LEVEL: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
    - LOGGING_FORMAT: json, console (default: console)
    """
    log_level_name = os.getenv("LOGGING_LEVEL", "INFO").upper()
    log_format = os.getenv("LOGGING_FORMAT", "console").lower()

    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if log_level_name not in valid_levels:
        print(f"Invalid LOGGING_LEVEL: {log_level_name}. Using INFO instead.")
        log_level_name = "INFO"
    
    log_level = getattr(logging, log_level_name)
    
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )
    
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    if log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a configured logger with the given name."""
    return structlog.get_logger(name)