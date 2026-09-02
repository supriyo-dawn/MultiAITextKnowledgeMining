"""
Structured logging setup.
Never logs credentials, API keys, or sensitive data.
"""

import logging
import logging.config
from datetime import datetime


def setup_logging(debug: bool = False) -> None:
    """
    Configure structured logging for the application.

    Args:
        debug: If True, set log level to DEBUG; otherwise INFO.
    """
    log_level = logging.DEBUG if debug else logging.INFO

    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_level,
                "formatter": "detailed",
                "filename": f"logs/app_{datetime.now().strftime('%Y%m%d')}.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
        },
        "root": {
            "level": log_level,
            "handlers": ["console", "file"],
        },
        "loggers": {
            "uvicorn": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(log_config)
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured (level: {logging.getLevelName(log_level)})")
