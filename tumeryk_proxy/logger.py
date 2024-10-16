#Copyright © 2024 Tumeryk, Inc.

import os
import csv
from datetime import datetime

LOG_DIRECTORY = os.getenv("LOG_DIRECTORY", "./logs")

def setup_csv_file(user: str):
    """Ensure the CSV log file exists and has headers."""
    today = datetime.now().strftime("%Y-%m-%d")
    user_log_dir = os.path.join(LOG_DIRECTORY, user)
    os.makedirs(user_log_dir, exist_ok=True)

    csv_file_path = os.path.join(user_log_dir, f"{today}.csv")

    # Write headers if the file is new or empty
    if not os.path.isfile(csv_file_path) or os.path.getsize(csv_file_path) == 0:
        headers = [
            "Timestamp",
            "User",
            "Message",
            "BotResponseTime",
            "GuardResponseTime",
            "Engine",
            "Model",
            "ConfigID",
            "BotResponse",
            "GuardResponse",
            "Violation",
            "BotTokens",
            "GuardTokens"
        ]
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
            writer.writerow(headers)

    return csv_file_path

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
    bot_tokens,
    guard_tokens
):
    """Log the interaction directly to a CSV file."""
    csv_file_path = setup_csv_file(user)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    # Create a list of fields
    fields = [
        timestamp,
        user,
        message,
        f"{bot_response_time}",
        f"{guard_response_time}",
        engine,
        model,
        config_id,
        bot_response,
        guard_response,
        str(violation),
        str(bot_tokens),
        str(guard_tokens)
    ]

    # Write the fields to the CSV file
    with open(csv_file_path, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
        writer.writerow(fields)

def fetch_logs(user: str):
    """Fetch logs for a specific user."""
    today = datetime.now().strftime("%Y-%m-%d")
    user_log_dir = os.path.join(LOG_DIRECTORY, user)
    csv_file_path = os.path.join(user_log_dir, f"{today}.csv")

    logs = []
    if os.path.exists(csv_file_path):
        with open(csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, quoting=csv.QUOTE_ALL)
            for row in reader:
                logs.append(row)
    else:
        print(f"Log file not found: {csv_file_path}")

    return logs
