import logging
import sys

from app.core.config import settings


logging.basicConfig(

    level=settings.LOG_LEVEL,

    format="%(asctime)s | %(levelname)s | %(message)s",

    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(settings.APP_NAME)