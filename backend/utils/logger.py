import logging
import re
from utils.config import get_settings

_setup_done = False

class APIKeyRedactor(logging.Filter):
    def filter(self, record):
        if isinstance(record.msg, str):
            record.msg = re.sub(r'([A-Za-z0-9_-]{20,})', '***REDACTED***', record.msg)
        return True

def get_logger(name: str) -> logging.Logger:
    global _setup_done
    if not _setup_done:
        settings = get_settings()
        level = getattr(logging, settings.log_level.upper(), logging.INFO)
        logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
        _setup_done = True
    
    logger = logging.getLogger(name)
    if not any(isinstance(f, APIKeyRedactor) for f in logger.filters):
        logger.addFilter(APIKeyRedactor())
    return logger
