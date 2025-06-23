"""
Logging configuration for the analytics assistant.
Provides structured logging across all components.
"""

import logging
import sys
from pathlib import Path


def setup_logger(name: str, level: str | None = None) -> logging.Logger:
    """
    Set up a logger with consistent formatting.

    Args:
        name: Logger name (typically __name__)
        level: Optional log level override

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Don't add handlers if they already exist
    if logger.handlers:
        return logger

    # Set log level from environment or default to INFO
    log_level = (level or "INFO").upper()
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional - only if logs directory exists)
    logs_dir = Path("logs")
    if logs_dir.exists() or logs_dir.parent.exists():
        try:
            logs_dir.mkdir(exist_ok=True)
            file_handler = logging.FileHandler(logs_dir / "analytics_assistant.log")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except (OSError, PermissionError):
            # If we can't create log files, just use console logging
            pass

    return logger


def log_api_call(
    logger: logging.Logger,
    service: str,
    operation: str,
    success: bool,
    duration: float | None = None,
    error: str | None = None,
) -> None:
    """
    Log API call results with structured information.

    Args:
        logger: Logger instance
        service: Service name (e.g., 'claude', 'ecb')
        operation: Operation name (e.g., 'parse_query', 'fetch_rates')
        success: Whether the operation succeeded
        duration: Operation duration in seconds
        error: Error message if operation failed
    """
    log_data = {
        "service": service,
        "operation": operation,
        "success": success,
        "duration_seconds": duration,
    }

    if success:
        message = f"{service}.{operation} succeeded"
        if duration:
            message += f" in {duration:.2f}s"
        logger.info(message, extra=log_data)
    else:
        message = f"{service}.{operation} failed"
        if error:
            message += f": {error}"
        logger.error(message, extra=log_data)


def log_data_query(
    logger: logging.Logger,
    source: str,
    dataset_type: str,
    parameters: dict,
    success: bool,
    record_count: int | None = None,
    error: str | None = None,
) -> None:
    """
    Log data query operations.

    Args:
        logger: Logger instance
        source: Data source ID
        dataset_type: Type of dataset queried
        parameters: Query parameters
        success: Whether the query succeeded
        record_count: Number of records returned
        error: Error message if query failed
    """
    log_data = {
        "data_source": source,
        "dataset_type": dataset_type,
        "parameters": parameters,
        "success": success,
        "record_count": record_count,
    }

    if success:
        message = f"Data query successful: {source}.{dataset_type}"
        if record_count is not None:
            message += f" ({record_count} records)"
        logger.info(message, extra=log_data)
    else:
        message = f"Data query failed: {source}.{dataset_type}"
        if error:
            message += f": {error}"
        logger.error(message, extra=log_data)
