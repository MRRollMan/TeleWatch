import os
import logging
from logging.handlers import TimedRotatingFileHandler

from TeleWatch import TeleWatch

def init_logger():
    if not os.path.exists("logs"):
        os.makedirs("logs")

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    log_file_name = "logs/log.log"
    file_handler = TimedRotatingFileHandler(
        log_file_name, when="midnight", interval=1, backupCount=30, encoding="utf-8"
    )
    file_handler.suffix = "%d-%m-%Y.log"
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%d.%m.%Y, %H:%M:%S"
        )
    )
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%d.%m.%Y, %H:%M:%S")
    )
    logger.addHandler(console_handler)


init_logger()

tw = TeleWatch()

if __name__ == '__main__':
    tw.start()
