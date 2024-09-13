
# Tumeryk Proxy

## Overview
Tumeryk Proxy is designed for secure interaction with LLMs and the Guard system. The two primary features are to interact with the model directly via the `chat` function and with the guard via `chat_guard` fucntion for a selected policy. Both of these functions can be found in the api client. More information regarding usage can be found below under "Running Tumeryk Proxy API Client."

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

5. Run the application:
   ```bash
   uvicorn main:app --reload
   ```

## Running Tumeryk Proxy API Client

### Overview
The `ApiClient` class allows direct interaction with the Tumeryk Proxy API.

### Example Usage

```python
from proxy_core.api_client import ApiClient

client = ApiClient()
client.login("username", "password")
client.set_config("hr_policy")
response = client.chat("What is the capital of France?")
print(response)
```

### Initialization

#### Constructor

```python
ApiClient(base_url="http://chat.tmryk.com", jwt_secret=os.getenv("JWT_SECRET_KEY"))
```

- **base_url** (str): The base URL for the API. Default is `"http://chat.tmryk.com"`.
- **jwt_secret** (str): The secret key used for JWT authentication. Default is fetched from environment variable `JWT_SECRET_KEY`.

### API Client Features

#### Setting the Configuration (Required Before Other Operations)

Before interacting with language models or the Guard, you must set a configuration ID, which defines the settings or model configurations to be used.

- **Method:** `set_config(config_id: str) -> dict`
- **Description:** Sets the configuration to be used by the user.
  
  **Parameters:**
  - `config_id`: The ID of the configuration you want to apply.
  
  **Example:**
  ```python
   client.set_config("hr_policy")
  ```

#### Authentication

You need to authenticate using your Tumeryk username and password to retrieve an access token and use other features.

- **Method:** `login(username: str, password: str) -> dict`
- **Description:** Authenticates the user and stores the JWT access token.
  
  **Parameters:**
  - `username`: Your Tumeryk username.
  - `password`: Your Tumeryk password.
  
  **Example:**
  ```python
  auth_response = client.login("my_username", "my_password")
  print(auth_response)
  ```

#### Sending a Message to a Language Model

You can directly interact with LLMs by sending a message and getting a response from the chosen model. **Note:** You must set a configuration using `set_config` before sending a message.

- **Method:** `chat(user_input: str) -> str`
- **Description:** Sends a message to the LLM and returns its response.
  
  **Parameters:**
  - `user_input`: The text input or question you want to ask the LLM.
  
  **Example:**
  ```python
  response = client.chat("Implement a binary tree.")
  print(response)
  ```

#### Sending a Message to the Guard

The `chat_guard` method allows you to send a message to Tumeryk's Guard system, which processes the request for additional security checks or constraints.

- **Method:** `chat_guard(user_input: str) -> dict`
- **Description:** Sends a message to the Guard service and returns its processed response.
  
  **Parameters:**
  - `user_input`: The text input to be processed by the Guard.
  
  **Example:**
  ```python
  response = client.chat_guard("Implement a binary tree.")
  print(response)
  ```

## UI vs. API Client

- **UI**: The Tumeryk Proxy UI offers an intuitive interface with integrated logging and configuration management. It is designed for easy, secure communication with models and the Guard system.
  
- **API Client**: The `ApiClient` class provides direct, programmatic interaction with Tumeryk services. While it doesn’t include built-in logging, it allows granular control over API requests and is easily extensible.

## Dependencies

- `os`
- `requests`
- `jwt`
- `langchain`
- `dotenv`
- `proxy_core` (custom module)

## Environment Variables

- **JWT_SECRET_KEY**: The secret key used for JWT authentication. You need to define this in the `.env` file.
