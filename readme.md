
# Proxy Guard Core

## Overview
Proxy Guard is designed for secure interaction with various language models directly and the guard.

## Setup Instructions

### Prerequisites
- Python 3.8+
- `pip` package manager
- Environment variables set in a `.env` file

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/tumeryk/Tumeryk-Gen-AI-Security-Developer-SDK.git
   cd
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Create a `.env` file in the project root.
   - Add your environment variables, e.g.:
     ```
     JWT_SECRET_KEY=your_jwt_secret
     ```

4. Request access to Tumeryk:
   - Sign up at https://tumeryk.com/sign-up to create your user ID and password.

6. Run the application:
   ```bash
   uvicorn main:app --reload
   ```

   
# Running Proxy Api Client Directly

## Overview

`ApiClient` is a Python class designed to interact with the Proxy Guard Core API. It handles authentication, manages API keys, and allows you to interact with different Language Learning Models (LLMs) like OpenAI, Cohere, Anthropic, and HuggingFaceHub.

## Initialization

### Constructor

```python
ApiClient(base_url="http://chat-dev.tmryk.com", jwt_secret=os.getenv("JWT_SECRET_KEY"))
```

- **base_url** (str): The base URL for the API. Default is `"http://chat-dev.tmryk.com"`.
- **jwt_secret** (str): The secret key used for JWT authentication. Default is fetched from environment variable `JWT_SECRET_KEY`.

### Example Usage

```python
client = ApiClient()
```

## Methods

### `login(username: str, password: str) -> dict`

Authenticates the user using the provided credentials and stores the access token.

- **username** (str): The username for authentication.
- **password** (str): The password for authentication.

**Returns:** A dictionary containing the response data from the authentication request.

### `chat(user_input: str) -> str`

Sends user input directly to the LLM and returns the response.

- **user_input** (str): The question or input to be processed by the LLM.

**Returns:** The response from the LLM as a string.

### `chat_guard(user_input: str) -> dict`

Sends user input to the Guard service.

- **user_input** (str): The question or input to be processed by the Guard service.

**Returns:** The response from the Guard service as a dictionary.

### `set_config(config_id: str) -> dict`

Sets the configuration ID to be used by the user.

- **config_id** (str): The configuration ID.

**Returns:** A dictionary indicating the config to use or an error message.

## Internal Methods

### `_get_headers() -> dict`

Generates the headers required for authenticated requests, including the authorization token.

**Returns:** A dictionary containing the headers.

### `_get_llm_chain(config_id: str) -> LLMChain`

Creates and returns an LLM chain with a prompt template. Uses caching to optimize performance.

- **config_id** (str): The configuration ID for fetching the API key.

**Returns:** An instance of `LLMChain`.

### `_fetch_api_key(config_id: str) -> dict`

Fetches the API key for the given config ID, using a cache for efficiency.

- **config_id** (str): The configuration ID for fetching the API key.

**Returns:** A dictionary containing the API key data.

### `_extract_model_details(api_key_data: dict) -> tuple`

Extracts model name and API key from the API key data.

- **api_key_data** (dict): The dictionary containing the API key details.

**Returns:** A tuple containing the model name and API key.

### `initialize_llm(service_name: str, api_key_value: str) -> LLM`

Initializes the LLM based on the service name and API key.

- **service_name** (str): The name of the LLM service (e.g., `openai`, `cohere`).
- **api_key_value** (str): The API key for the LLM service.

**Returns:** An instance of the appropriate LLM class.

### `_create_llm_chain(llm) -> LLMChain`

Creates an `LLMChain` with a predefined prompt template.

- **llm**: The initialized LLM instance.

**Returns:** An instance of `LLMChain`.

## Dependencies

- `os`
- `requests`
- `jwt`
- `langchain`
- `dotenv`
- `utils.user_data` (custom module)

## Environment Variables

- `JWT_SECRET_KEY`: The secret key used for JWT authentication.

## Example Usage

```python
from utils.api_client import ApiClient

client = ApiClient()
client.login("username", "password")
response = client.chat("What is the capital of France?")
print(response)
```



