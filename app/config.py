import os
import logging

# Constants
TEMPLATE_DIR = "templates"
STATIC_DIR = f"{TEMPLATE_DIR}/static"


def setup_logging():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    return logger
