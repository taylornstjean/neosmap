import logging
from logging.handlers import RotatingFileHandler
from config import LOG_DIR
import os


###########################################################################
# PROGRAM LOGGER

class LogFormatterConsole(logging.Formatter):

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    _format = "%(asctime)s - %(name)s - [%(levelname)s] - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + _format + reset,
        logging.INFO: grey + _format + reset,
        logging.WARNING: yellow + _format + reset,
        logging.ERROR: red + _format + reset,
        logging.CRITICAL: bold_red + _format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class LogFormatterFile(logging.Formatter):

    _format = "%(asctime)s - %(name)s - [%(levelname)s] - %(message)s (%(filename)s:%(lineno)d)"

    def format(self, record):
        formatter = logging.Formatter(self._format)
        return formatter.format(record)


logger = logging.getLogger("NEOSMAP")
logger.setLevel(logging.DEBUG)

# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setFormatter(LogFormatterConsole())
ch.setLevel(logging.DEBUG)

logger.addHandler(ch)

log_path = os.path.join(LOG_DIR, "neosmap.log")

fh = RotatingFileHandler(log_path, mode='a', maxBytes=5*1024*1024, backupCount=2, encoding=None, delay=False)
fh.setFormatter(LogFormatterFile())
fh.setLevel(logging.DEBUG)

logger.addHandler(fh)


# https://stackoverflow.com/questions/384076/

# ------------------------------ END OF FILE ------------------------------
