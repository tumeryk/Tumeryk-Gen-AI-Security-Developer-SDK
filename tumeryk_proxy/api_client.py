import os
import requests
import jwt
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain_anthropic import AnthropicLLM

from langchain_community.llms import Cohere, HuggingFaceHub
from user_data import get_user_data
from dotenv import load_dotenv
import yaml

load_dotenv()


class ApiClient:
    """API Client for Proxy Guard Core"""

    def __init__(self, base_url=os.getenv("BASE_URL","https://chat.tmryk.com")):
        self.base_url = base_url
        self.token = None
        self.user_data = None  # Initialize user data as None

    def login(self, username: str, password: str):
        """Authenticate and store access token and user data."""
        print(username,password,self.base_url)
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

    def _get_llm_chain(self, config_id: str) -> LLMChain:
        """Create and return an LLM chain with a prompt template."""
        # Check if the LLMChain is already cached
        if config_id in self.user_data.llm_chain_cache:
            return self.user_data.llm_chain_cache[config_id]

        # Check if the model is already cached
        if config_id in self.user_data.models:
            llm = self.user_data.models[config_id]["llm"]
        else:
            # Retrieve the API key and initialize the model if not cached
            model, engine = self._fetch_model_and_engine_from_config(config_id)
            api_key_data = self._fetch_api_key(config_id)
            api_key_value = api_key_data.get("api_key_value")
            llm = self.initialize_llm(engine, api_key_value, model)
            self.user_data.models[config_id] = {
                "llm": llm,
                "engine": engine,
                "model": model,
            }

        # Create and cache the LLMChain
        llm_chain = self._create_llm_chain(llm)
        self.user_data.llm_chain_cache[config_id] = llm_chain

        return llm_chain

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

        # Cache the API key for future use
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

        # Extract the YAML content from the response
        yaml_content = config_data.get("config.yml")
        if not yaml_content:
            raise ValueError(f"YAML configuration for '{config_name}' not found.")

        # Parse the YAML content
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
        """Initialize the LLM based on the model name and API key."""
        if service_name == "openai":
            return ChatOpenAI(model=model, openai_api_key=api_key_value)
        elif service_name == "cohere":
            return Cohere(api_key=api_key_value)
        elif service_name == "anthropic":
            return AnthropicLLM(anthropic_api_key=api_key_value)
        elif service_name == "huggingface":
            return HuggingFaceHub(
                repo_id="gpt2", huggingfacehub_api_token=api_key_value
            )
        else:
            raise ValueError("Unsupported model name")

    @staticmethod
    def _create_llm_chain(llm) -> LLMChain:
        """Create an LLMChain with a predefined prompt template."""
        prompt_template = PromptTemplate(
            input_variables=["question"],
            template="You are a helpful assistant. Answer the following question: {question}",
        )
        return LLMChain(llm=llm, prompt=prompt_template)

    def chat(self, user_input: str) -> str:
        """Send user input to the LLM directly and return the response."""
        if not self.user_data:
            return {"error": "User data not set. Please login"}
        config_id = self.user_data.config_id
        if not config_id:
            return {"error": "Config ID is required. Please pick a policy"}
        llm_chain = self._get_llm_chain(config_id)
        return llm_chain.run(question=user_input)

    def chat_guard(self, user_input: str):
        """Send user input to the Guard service."""
        if not self.user_data:
            return {"error": "User data not set. Please login"}
        config_id = self.user_data.config_id
        if not config_id:
            return {"error": "Config ID is required. Please pick a policy"}

        headers = self._get_headers()
        guard_url = f"{self.base_url}/v1/chat/completions"
        role = {"role": "user", "content": user_input}
        payload = {"config_id": config_id, "messages": [role], "stream": False}

        try:
            response = requests.post(guard_url, json=payload, headers=headers)
            response.raise_for_status()
            msg = response.json()
            print("msg", msg)
            return [
                msg.get("messages")[-1].get("content"),
                msg.get("messages")[-1].get("violation"),
            ]
        except Exception as err:
            return {"error": str(err)}

    def set_config(self, config_id: str):
        """Set the configuration ID to be used by the user."""
        if not self.user_data:
            raise ValueError("User data not set. Please login first.")
        
        self.user_data.config_id = config_id
        return {"config": f"config to use in proxy: {config_id}"}


client = ApiClient()
