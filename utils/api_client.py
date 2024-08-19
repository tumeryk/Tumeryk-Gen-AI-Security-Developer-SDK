import os
import requests
import jwt
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain_community.llms import Cohere, Anthropic, HuggingFaceHub
from utils.user_data import get_user_data


class ApiClient:
    """API Client for Proxy Guard Core"""

    def __init__(self, base_url="http://chat-dev.tmryk.com", jwt_secret=None):
        self.base_url = base_url
        self.token = None
        self.jwt_secret = jwt_secret or os.getenv("JWT_SECRET_KEY")
        self.user_data = None  # Initialize user data as None

    def login(self, username: str, password: str):
        """Authenticate and store access token and user data."""
        payload = {"grant_type": "password", "username": username, "password": password}
        response = requests.post(f"{self.base_url}/auth/token", data=payload)
        response.raise_for_status()
        response_data = response.json()

        if "access_token" in response_data:
            self.token = response_data["access_token"]
            self.user_data = get_user_data(username)  # Initialize user data after login

        return response_data

    def _get_headers(self):
        """Helper method to get the headers including authorization."""
        if not self.token:
            raise ValueError("Authorization token is not set. Please login first.")

        return {"Authorization": f"Bearer {self.token}"}

    def _get_llm_chain(self, config_id: str) -> LLMChain:
        """Create and return an LLM chain with a prompt template."""
        # Check if the model (and thus API key) is already cached
        if config_id in self.user_data.models:
            llm = self.user_data.models[config_id]["llm"]
        else:
            # Retrieve the API key and initialize the model if not cached
            api_key_data = self._fetch_api_key(config_id)
            model_name, api_key_value = self._extract_model_details(api_key_data)
            llm = self.initialize_llm(model_name, api_key_value)
            self.user_data.models[config_id] = {"model": llm, "model_name": model_name}

        # Create and return the LLM chain
        return self._create_llm_chain(llm)

    def _fetch_api_key(self, config_id: str) -> dict:
        """Fetch the API key for the given config ID."""
        headers = self._get_headers()
        response = requests.get(
            f"{self.base_url}/llm_api_key",
            headers=headers,
            params={"config_id": config_id},
        )
        response.raise_for_status()
        api_key_data = response.json().get("api_key_value_pair")

        if api_key_data is None:
            raise ValueError(
                f"No API key was found for Config ID: {config_id}. Response: {response.json()}"
            )

        return api_key_data

    @staticmethod
    def _extract_model_details(api_key_data: dict) -> tuple:
        """Extract model name and API key from the API key data."""
        model_name = api_key_data.get("api_key_name").split("_")[0]
        api_key_value = api_key_data.get("api_key_value")
        return model_name, api_key_value

    @staticmethod
    def initialize_llm(service_name: str, api_key_value: str):
        """Initialize the LLM based on the model name and API key."""
        if service_name == "openai":
            return ChatOpenAI(
                model="gpt-3.5-turbo", temperature=0.6, openai_api_key=api_key_value
            )
        elif service_name == "cohere":
            return Cohere(api_key=api_key_value)
        elif service_name == "anthropic":
            return Anthropic(api_key=api_key_value)
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
        config_id = self.user_data.config_id  # Assume config_id is already set
        llm_chain = self._get_llm_chain(config_id)
        return llm_chain.run(question=user_input)

    def chat_guard(self, user_input: str):
        """Send user input to the Guard service."""
        config_id = self.user_data.config_id
        if not config_id:
            return {"error": "Config ID is required"}

        headers = self._get_headers()
        guard_url = f"{self.base_url}/v1/chat/completions"
        role = {"role": "user", "content": user_input}
        payload = {"config_id": config_id, "messages": [role], "stream": False}

        try:
            response = requests.post(guard_url, json=payload, headers=headers)
            response.raise_for_status()
            msg = response.json()
            return msg.get("messages")[-1].get("content")
        except Exception as err:
            return {"error": str(err)}

    def set_config(self, config_id: str):
        """Set the configuration ID to be used by the user."""
        if not self.token:
            raise ValueError("Authorization token is not set. Please login first.")

        try:
            decode = jwt.decode(self.token, algorithms="HS256", key=self.jwt_secret)
            user_info = decode.get("sub")
            self.user_data = get_user_data(user_info)
            self.user_data.config_id = config_id
            return {"config": f"config to use in proxy: {config_id}"}
        except jwt.ExpiredSignatureError:
            return {"error": "Token has expired"}
        except jwt.InvalidTokenError:
            return {"error": "Invalid token"}
        except Exception as e:
            return {"error": str(e)}

client = ApiClient()