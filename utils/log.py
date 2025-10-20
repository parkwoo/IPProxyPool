"""Provide logging functionality"""
import sys

import logging
from settings import LOG_FMT, LOG_DATEFMT, LOG_FILENAME, LOG_LEVEL


class Logger(object):
    """Logger class"""
    def __init__(self):
        # Get a logger object
        self._logger = logging.getLogger()
        # Set format object
        self.formatter = logging.Formatter(fmt=LOG_FMT,datefmt=LOG_DATEFMT)
        # Set log output
        # Set file log mode
        self._logger.addHandler(self._get_file_handler(LOG_FILENAME))
        # Set console log mode
        self._logger.addHandler(self._get_console_handler())
        # Set log level
        self._logger.setLevel(LOG_LEVEL)

    def _get_file_handler(self, filename):
        '''Return a file log handler'''
        # Get a file log handler
        filehandler = logging.FileHandler(filename=filename,encoding="utf-8")
        # Set log format
        filehandler.setFormatter(self.formatter)
        # Return handler
        return filehandler

    def _get_console_handler(self):
        '''Return a console log handler'''
        # Get a console log handler
        console_handler = logging.StreamHandler(sys.stdout)
        # Set log format
        console_handler.setFormatter(self.formatter)
        # Return handler
        return console_handler

    @property
    def logger(self):
        return self._logger

# Initialize and configure a logger object to achieve singleton
# When using, directly import logger to use
logger = Logger().logger

if __name__ == '__main__':
    logger.debug("Debug information")
    logger.info("Status information")
    logger.warning("Warning information")
    logger.error("Error information")
    logger.critical("Critical error information")