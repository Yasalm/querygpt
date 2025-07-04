import sys
from pathlib import Path
from loguru import logger
import os


def setup_logging(
    log_level: str = "INFO",
    log_file: str = None,
    rotation: str = "10 MB",
    retention: str = "7 days",
    format: str = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
):
    """
    Setup loguru logging configuration for the project.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        rotation: Log rotation size (e.g., "10 MB", "1 day")
        retention: Log retention period (e.g., "7 days", "1 month")
        format: Log message format
    """

    logger.remove()
    

    logger.add(
        sys.stderr,
        format=format,
        level=log_level,
        colorize=True
    )
    
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_file,
            format=format,
            level=log_level,
            rotation=rotation,
            retention=retention,
            compression="zip"
        )
    
    return logger


def get_logger(name: str = None):
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Logger instance
    """
    if name:
        return logger.bind(name=name)
    return logger


def init_logging():
    """Initialize logging with default configuration from environment variables."""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_file = os.getenv("LOG_FILE", None)
    
    setup_logging(
        log_level=log_level,
        log_file=log_file
    )
    
    return logger


default_logger = init_logging() 