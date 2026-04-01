import logging
from datetime import datetime

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler(f'bot_{datetime.now().strftime("%Y%m%d")}.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def get_logger(name):
    return logging.getLogger(name)

def log_error(logger, error, user_id=None, context=None):
    error_msg = f"Xatolik: {error}"
    if user_id:
        error_msg += f" | User ID: {user_id}"
    if context:
        error_msg += f" | Context: {context}"
    logger.error(error_msg, exc_info=True)