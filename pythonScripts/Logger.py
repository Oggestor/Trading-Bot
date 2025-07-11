import logging
import dotenv
import os
from datetime import datetime

# Load environment variables
dotenv.load_dotenv()
LOG_PATH = os.getenv('LOG_PATH')

# Configure logger instance
logger = logging.getLogger("CustomLogger")
logger.setLevel(logging.DEBUG)  # Default level (adjustable)

# Ensure log path exists
def validate_log_file():
    if not os.path.exists(LOG_PATH):
        os.makedirs(LOG_PATH)
    return os.path.join(LOG_PATH, "log-" + datetime.now().strftime("%Y-%m-%d") + ".log")

# Initialize logging handlers (only once)
log_filename = validate_log_file()
file_handler = logging.FileHandler(log_filename)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'))

# Add handlers if not already added
if not logger.hasHandlers():
    logger.addHandler(file_handler)

# Logging function
def log(message, log_type="INFO"):
    if log_type == "ERROR":
        logger.error(message, stacklevel=2)  # stacklevel=2 captures caller's details
    elif log_type == "INFO":
        logger.info(message, stacklevel=2)
    elif log_type == "DEBUG":
        logger.debug(message, stacklevel=2)
    elif log_type == "WARNING":
        logger.warning(message, stacklevel=2)
    else:
        logger.info(message, stacklevel=2)
