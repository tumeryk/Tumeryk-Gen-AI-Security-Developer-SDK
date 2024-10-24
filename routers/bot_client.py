#Copyright © 2024 Tumeryk, Inc.

import os
import requests
import yaml
from litellm import completion
from dotenv import load_dotenv
from .user_data import get_user_data

load_dotenv()

class BotClient:
    """Client for handling bot responses with proper model management"""
    def __init__(self, base_url=os.getenv("TUMERYK_BASE_URL", "https://chat.tmryk.com")):
        self.base_url = base_url
        self.token = None
        self.user_data = None

    def set_token(self, token: str, username: str):
        """Set the token and initialize user data."""
        self.token = token
        self.user_data = get_user_data(username)

    def _get_headers(self):
        """Get headers with authorization."""
        if not self.token:
            raise ValueError("Authorization token is not set")
        return {"Authorization": f"Bearer {self.token}"}

    def _fetch_api_key(self, config_id: str) -> str:
        """Fetch API key for the given config ID."""
        if config_id in self.user_data.api_key_cache:
            return self.user_data.api_key_cache[config_id]

        headers = self._get_headers()
        response = requests.get(
            f"{self.base_url}/llm_api_key",
            headers=headers,
            params={"config_id": config_id},
        )
        response.raise_for_status()
        api_key_data = response.json()
        
        if "api_key_value" not in api_key_data:
            raise ValueError(f"No API key found for Config ID: {config_id}")
        
        api_key = api_key_data.get("api_key_value")
        self.user_data.api_key_cache[config_id] = api_key
        return api_key

    def _fetch_model_config(self, config_id: str) -> tuple:
        """Fetch model and engine from config."""
        headers = self._get_headers()
        response = requests.get(
            f"{self.base_url}/read_config",
            headers=headers,
            params={"config_name": config_id},
        )
        response.raise_for_status()
        
        config_data = response.json()
        yaml_content = config_data.get("config.yml")
        if not yaml_content:
            raise ValueError(f"Config not found for: {config_id}")

        config = yaml.safe_load(yaml_content)
        model_info = config.get("models", [{}])[0]
        model = model_info.get("model")
        engine = model_info.get("engine")

        if not model or not engine:
            raise ValueError("Model or engine not found in config")
            
        return model, engine

    def get_completion(self, messages: list, config_id: str):
        """Get bot completion using proper model configuration."""
        if config_id not in self.user_data.models:
            # Fetch and cache model info
            model, engine = self._fetch_model_config(config_id)
            api_key = self._fetch_api_key(config_id)
            
            self.user_data.models[config_id] = {
                "model": model,
                "engine": engine,
                "api_key": api_key
            }
        
        model_info = self.user_data.models[config_id]
        
        # Use litellm with the configured model
        if 'gpt-3.5-turbo-instruct' in model_info["model"]:
            return completion(
                model=model_info["model"],
                messages=messages,
                api_key=model_info["api_key"],
                max_tokens=3000
            )
        else:
            return completion(
                model=model_info["model"],
                messages=messages,
                api_key=model_info["api_key"]
            )

# Global instance
bot_client = BotClient()
