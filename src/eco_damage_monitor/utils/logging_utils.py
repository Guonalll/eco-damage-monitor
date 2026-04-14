from __future__ import annotations

import logging

try:
    from loguru import logger
except ModuleNotFoundError:  # pragma: no cover - fallback for lean environments
    logger = None


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        if logger is not None:
            logger.opt(exception=record.exc_info).log(record.levelname, record.getMessage())
        else:
            logging.getLogger(record.name).handle(record)


def setup_logging(level: str = "INFO") -> None:
    if logger is None:
        logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO))
        return
    logging.basicConfig(handlers=[InterceptHandler()], level=level)
    logger.remove()
    logger.add(lambda msg: print(msg, end=""), level=level)
