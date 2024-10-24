#Copyright © 2024 Tumeryk, Inc.

from typing import List, Dict, Any
import json
import os
from datetime import datetime

class UserData:
    def __init__(self, username: str):
        self.username = username
        # Chat history
        self.chat_log: List[str] = []
        self.chat_responses: List[str] = []
        # Guard history
        self.guard_log: List[Dict[str, Any]] = []
        self.guard: List[str] = []
        # Model and config data
        self.configs: List[str] = []
        self.models: Dict[str, Dict[str, str]] = {}  # {config_id: {model, engine, api_key}}
        self.api_key_cache: Dict[str, str] = {}  # {config_id: api_key}

# In-memory storage for user data
user_data_store: Dict[str, UserData] = {}

def get_user_data(username: str) -> UserData:
    """Get or create user data for the given username."""
    if username not in user_data_store:
        user_data_store[username] = UserData(username)
    return user_data_store[username]

def log_interaction(
    user: str,
    message: str,
    bot_response_time: str,
    guard_response_time: str,
    engine: str,
    model: str,
    config_id: str,
    bot_response: str,
    guard_response: str,
    violation: bool,
    bot_tokens: int,
    guard_tokens: int
) -> None:
    """Log user interaction details to a file."""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, f"{user}_interactions.jsonl")
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "user": user,
        "message": message,
        "bot_response_time": bot_response_time,
        "guard_response_time": guard_response_time,
        "engine": engine,
        "model": model,
        "config_id": config_id,
        "bot_response": bot_response,
        "guard_response": guard_response,
        "violation": violation,
        "bot_tokens": bot_tokens,
        "guard_tokens": guard_tokens
    }
    
    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

def fetch_logs(username: str) -> List[Dict[str, Any]]:
    """Fetch logs for a specific user."""
    log_file = os.path.join("logs", f"{username}_interactions.jsonl")
    logs = []
    
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            for line in f:
                logs.append(json.loads(line.strip()))
    
    return logs
