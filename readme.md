
# Tumeryk Proxy

## Overview
Tumeryk Proxy is designed for secure interaction with LLMs and the Tumeryk Guard system. The two primary features are to interact with the model directly via the `chat` function and with the guard via the `chat_guard` function for a selected policy. Both of these functions can also be found in the API client. More information regarding usage can be found below under "Running Tumeryk Proxy API Client."

## UI vs. API Client

- **Tumeryk Proxy** can be run in two ways: (1) via the pre-built Client UI or (2) programmatically with the API client. The instructions below demonstrate programmatic usage in Python.


- **UI**: The Tumeryk Proxy UI offers a limited interface for demo purposes. More information about the UI can be found in [docs.md](https://github.com/tumeryk/Tumeryk-Gen-AI-Security-Developer-SDK/blob/develop/docs.md)

- **API Client**: The `ApiClient` class provides direct, programmatic interaction with Tumeryk services. Logging can be integrated via use of `tumeryk_proxy/logger.py` More information about the API Client is listed [below](https://github.com/tumeryk/Tumeryk-Gen-AI-Security-Developer-SDK/blob/develop/readme.md#running-tumeryk-proxy-api-client). 


## Setup Instructions


### Running the Installer Shell Script

1. Download `Run_Tumeryk_Proxy.sh`.
2. Open the terminal and navigate to the script location.
3. Give the script execution permissions:

   ```bash
   chmod a+x Run_Tumeryk_Proxy.sh
   ```

4. Run the script:

   ```bash
   ./Run_Tumeryk_Proxy.sh
   ```

The script will set up the environment, install dependencies, and launch the FastAPI server.

Ensure Python is installed before running the script.

## Manual Setup
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
     BASE_URL="https://chat.tmryk.com"
     ```

4. Request access to Tumeryk:
   - Sign up at https://tumeryk.com/sign-up to create your user ID and password.

5. Run the UI via:
   ```bash
   uvicorn main:app --reload
   ```

## Running Tumeryk Proxy API Client

### Overview
The `ApiClient` class allows direct interaction with the Tumeryk Proxy API. 

You can use it to send messages to the LLM or Tumeryk Guard after authentication and configuration.

### Example Usage

```python
from tumeryk_proxy.api_client import ApiClient

client = ApiClient()
client.login("username", "password")
client.set_config("hr_policy")
response = client.chat_guard("What is the capital of France?")
print(response)
```

### Initialization

#### Constructor

```python
ApiClient(base_url="https://chat.tmryk.com")
```

- **base_url** (str): The base URL for the API. Default is `"https://chat.tmryk.com"`.

### API Client Features

#### Authentication (Required Before Other Operations)

You need to authenticate using your Tumeryk username and password to retrieve an access token and use other features. 

- **Method:** `login(username: str, password: str) -> dict`
- **Description:** Authenticates the user.
  
  **Parameters:**
  - `username`: Your Tumeryk username.
  - `password`: Your Tumeryk password.
  
  **Example:**
  ```python
    client.login("my_username", "my_password")
  ```

#### Setting the Configuration (Required Before Other Operations)

Before interacting with language models or the Guard, you must set a configuration/policy, which defines the model policy to be used.

- **Method:** `set_config(config_id: str) -> dict`
- **Description:** Sets the policy to be used by the user.
  
  **Parameters:**
  - `config_id`: The name of the policy you want to apply.
  
  **Example:**
  ```python
   client.set_config("hr_policy")
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

The `chat_guard` method allows you to send a message to Tumeryk's Guard system, which processes the request for additional security checks or constraints based on the policy.

- **Method:** `chat_guard(user_input: str) -> dict`
- **Description:** Sends a message to the Guard service and returns its processed response.
  
  **Parameters:**
  - `user_input`: The text input to be processed by the Guard.
  
  **Example:**
  ```python
  response = client.chat_guard("Implement a binary tree.")
  print(response)
  ```

## Dependencies for Tumeryk Proxy API Client + UI

- fastapi
- uvicorn
- openai
- requests
- aiofiles
- jinja2
- PyJWT
- python-multipart
- langchain
- langchain_community
- python-dotenv
- jwt


## Environment Variables

- **BASE_URL**: The base url for the proxy client. Default is `https://chat.tmryk.com`
- **JWT_SECRET_KEY** The JWT Token: used in the UI Client backend. 
