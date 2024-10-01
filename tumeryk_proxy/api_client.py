import os
import requests
from litellm import completion
from dotenv import load_dotenv
import yaml
from .user_data import get_user_data

load_dotenv()

class ApiClient:
    """API Client for Proxy Guard Core"""

    def __init__(self, base_url=os.getenv("BASE_URL", "https://chat.tmryk.com")):
        self.base_url = base_url
        self.token = None
        self.user_data = None  # Initialize user data as None

    def login(self, username: str, password: str):
        """Authenticate and store access token and user data."""
        payload = {"grant_type": "password", "username": username, "password": password}
        response = requests.post(f"{self.base_url}/auth/token", data=payload)
        response.raise_for_status()
        response_data = response.json()

        if "access_token" in response_data:
            self.token = response_data["access_token"]
            self.user_data = get_user_data(username)
        return response_data

    def _get_headers(self):
        """Helper method to get the headers including authorization."""
        if not self.token:
            raise ValueError("Authorization token is not set. Please login first.")
        return {"Authorization": f"Bearer {self.token}"}

    def _get_llm_chain(self, config_id: str):
        """Create and return an LLM chain with a prompt template."""
        if config_id in self.user_data.llm_chain_cache:
            return self.user_data.llm_chain_cache[config_id]

        # Check if the model is already cached
        if config_id in self.user_data.models:
            llm = self.user_data.models[config_id]["llm"]
        else:
            model, engine = self._fetch_model_and_engine_from_config(config_id)
            api_key_value = self._fetch_api_key(config_id).get("api_key_value")
            llm = self.initialize_llm(engine, api_key_value, model)
            self.user_data.models[config_id] = {
                "llm": llm,
                "engine": engine,
                "model": model,
            }

        self.user_data.llm_chain_cache[config_id] = llm
        return llm

    def _fetch_api_key(self, config_id: str) -> dict:
        """Fetch the API key for the given config ID, using a cache."""
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
            raise ValueError(
                f"No API key was found for Config ID: {config_id}. Response: {response.json()}"
            )

        self.user_data.api_key_cache[config_id] = api_key_data.get("api_key_value")
        return api_key_data

    def _fetch_model_and_engine_from_config(self, config_name: str) -> tuple:
        """Fetch the model and engine from the YAML configuration."""
        headers = self._get_headers()
        response = requests.get(
            f"{self.base_url}/read_config",
            headers=headers,
            params={"config_name": config_name},
        )
        response.raise_for_status()
        config_data = response.json()

        yaml_content = config_data.get("config.yml")
        if not yaml_content:
            raise ValueError(f"YAML configuration for '{config_name}' not found.")

        config = yaml.safe_load(yaml_content)
        model_info = config.get("models", [{}])[0]
        model_name = model_info.get("model")
        engine_name = model_info.get("engine")

        if not model_name or not engine_name:
            raise ValueError(
                "Model name or engine name not found in the YAML configuration."
            )

        return model_name, engine_name

    @staticmethod
    def initialize_llm(service_name: str, api_key_value: str, model: str):
        """Initialize the LLM using LiteLLM based on the model and engine."""
        
        def get_completion(messages):
            # Only apply max_tokens if the model is gpt-3.5-turbo-instruct
            if 'gpt-3.5-turbo-instruct' in model:
                return completion(model=model, messages=messages, api_key=api_key_value, max_tokens=3000)
            else:
                return completion(model=model, messages=messages, api_key=api_key_value)
        
        return get_completion


    def chat(self, user_input: str) -> str:
        """Send user input to the LLM and return the response."""
        if not self.user_data:
            return {"error": "User data not set. Please login."}
        config_id = self.user_data.config_id
        if not config_id:
            return {"error": "Config ID is required. Please pick a policy."}
        
        llm = self._get_llm_chain(config_id)
        response = llm([{"role": "user", "content": user_input}])
        print(response)
        return response

    def chat_guard(self, user_input: str):
        """Send user input to the Guard service."""
        if not self.user_data:
            return {"error": "User data not set. Please login."}
        config_id = self.user_data.config_id
        if not config_id:
            return {"error": "Config ID is required. Please pick a policy."}

        headers = self._get_headers()
        guard_url = f"{self.base_url}/v1/chat/completions"
        role = {"role": "user", "content": user_input}
        payload = {"config_id": config_id, "messages": [role], "stream": False}

        try:
            response = requests.post(guard_url, json=payload, headers=headers)
            response.raise_for_status()
            msg = response.json()
            return msg
        except Exception as err:
            return {"error": str(err)}

    def set_config(self, config_id: str):
        """Set the configuration ID to be used by the user."""
        if not self.user_data:
            raise ValueError("User data not set. Please login first.")
        
        self.user_data.config_id = config_id
        return {"config": f"config to use in proxy: {config_id}"}


client = ApiClient()
