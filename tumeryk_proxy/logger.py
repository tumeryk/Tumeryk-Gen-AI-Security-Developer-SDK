import os
import logging
from datetime import datetime
import csv
import re

LOG_DIRECTORY = os.getenv("LOG_DIRECTORY", "./logs")


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
            "Timestamp,User,Level,Message,BotResponseTime,GuardResponseTime,"
            "Engine,Model,ConfigID,BotResponse,GuardResponse,Violation"
        )
        logger.info(headers)

    return logger


def log_interaction(
    user: str,
    message: str,
    bot_response_time: float,
    guard_response_time: float,
    engine: str,
    model: str,
    config_id: str,
    bot_response: str,
    guard_response: str,
    violation: bool,
):
    """Log the interaction using Python's logging library in CSV format."""
    logger = setup_logger(user)

    log_message = (
        f'"{message}",{bot_response_time},{guard_response_time},"{engine},""{model}","{config_id}",'
        f'"{bot_response}","{guard_response}",{violation}'
    )

    logger.info(log_message)


def fetch_logs(user: str):
    """Fetch logs for a specific user."""
    today = datetime.now().strftime("%Y-%m-%d")
    user_log_dir = os.path.join(LOG_DIRECTORY, user)
    log_file_path = os.path.join(user_log_dir, f"{today}.log")
    
    logs = []
    if os.path.exists(log_file_path):
        with open(log_file_path, 'r') as file:
            for line in file:
                # Skip header lines
                if "Timestamp,User,Level,Message" in line:
                    continue
                
                # Parse the log line
                match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}), (\w+), (\w+), (.+)', line)
                if match:
                    timestamp, log_user, level, rest = match.groups()
                    # Parse the rest of the line using csv module to handle quoted fields
                    reader = csv.reader([rest])
                    fields = next(reader)
                    
                    # Create a dictionary with the parsed data
                    log_entry = {
                        "Timestamp": timestamp,
                        "User": log_user,
                        "Level": level,
                        "Message": fields[0],
                        "BotResponseTime": fields[1],
                        "GuardResponseTime": fields[2],
                        "Engine": fields[3],
                        "Model": fields[4],
                        "ConfigID": fields[5],
                        "BotResponse": fields[6],
                        "GuardResponse": fields[7],
                    }
                    logs.append(log_entry)
    
    return logs