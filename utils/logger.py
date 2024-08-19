import os
import logging
from datetime import datetime

LOG_DIRECTORY = "./logs"


def setup_logger(user: str):
    """Set up and return a logger configured to write to a user-specific file."""
    today = datetime.now().strftime("%Y-%m-%d")
    user_log_dir = os.path.join(LOG_DIRECTORY, user)
    os.makedirs(user_log_dir, exist_ok=True)

    log_file_path = os.path.join(user_log_dir, f"{today}.log")

    logger = logging.getLogger(user)
    logger.setLevel(logging.INFO)

    if not logger.hasHandlers():
        file_handler = logging.FileHandler(log_file_path)
        log_format = logging.Formatter(
            "%(asctime)s, %(name)s, %(levelname)s, %(message)s"
        )
        file_handler.setFormatter(log_format)
        logger.addHandler(file_handler)

        # Write headers to the CSV file
        headers = (
            "Timestamp,User,Level,Role,Message,BotResponseTime,GuardResponseTime,"
            "Model,ConfigID,BotResponse,GuardResponse,Violation"
        )
        logger.info(headers)

    return logger


def log_interaction(
    user: str,
    role: str,
    message: str,
    bot_response_time: float,
    guard_response_time: float,
    model: str,
    config_id: str,
    bot_response: str,
    guard_response: str,
    violation: bool,
):
    """Log the interaction using Python's logging library in CSV format."""
    logger = setup_logger(user)

    log_message = (
        f'{role},"{message}",{bot_response_time},{guard_response_time},"{model}","{config_id}",'
        f'"{bot_response}","{guard_response}",{violation}'
    )

    logger.info(log_message)
