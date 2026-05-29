"""Configure the logger for each called function"""

import logging
import logging.config

API_LOGGER_CONF = {
    "version": 1,
    "root": {"level": "INFO"},
    "handlers": {
        "wsgi": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "INFO",
        },
    },
    "formatters": {
        "default": {
            "format": "%(asctime)s %(name)-50s "
            "%(levelname)-8s %(funcName)-20s:%(lineno)-4d %(message)s"
        }
    },
    "loggers": {
        "gunicorn.access": {"level": "INFO", "handlers": ["wsgi"]},
        "gunicorn.error": {"level": "INFO", "handlers": ["wsgi"]},
        "uvicorn.access": {"level": "INFO", "handlers": ["wsgi"]},
        "uvicorn.error": {"level": "INFO", "handlers": ["wsgi"]},
        "app": {"level": "INFO", "handlers": ["wsgi"]},
    },
}


def configure_logging() -> None:
    logging.config.dictConfig(API_LOGGER_CONF)
