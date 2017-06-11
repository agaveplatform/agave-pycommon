__author__ = 'jstubbs'
import logging

logger = logging.getLogger(__name__)

class Error(Exception):
    def __init__(self, message=None):
        self.message = message
        if message:
            logger.info("Error raised:" + message)