
# Documentation

## Overview
This project is a FastAPI-based web application that allows users to log in, interact with various language models, and view logs and reports of their interactions. It utilizes JWT for user authentication and includes functionality to measure and log response times from both direct model interactions and a guard service.

## Project Structure
- **`main.py`**: The entry point of the application. It sets up the FastAPI app, includes routers, and configures static files and templates.
- **`routers/`**: Contains route handlers divided by functionality (e.g., authentication, chat interactions, configuration management).
- **`auth.py`**: Handles user authentication, including login and token management.
- **`chat.py`**: Manages the chat interactions, rendering the portal, handling user inputs, and generating reports.
- **`config.py`**: Manages configuration settings such as setting a configuration ID for the user.
- **`utils/`**: Contains utility modules used across the application.
  - **`api_client.py`**: Manages API interactions, including logging in users, handling tokens, and interacting with the language models.
  - **`user_data.py`**: Handles user-specific data management.
  - **`logger.py`**: Manages logging of interactions, storing them in user-specific log files.
- **`templates/`**: Contains Jinja2 HTML templates for rendering the web pages.
  - **`home.html`**: The chat portal page.
  - **`report.html`**: The reports page showing logs and responses.
- **`static/`**: Holds static files like CSS and JavaScript used in the frontend.


## API Endpoints

### Authentication
- **POST `/login`**: Authenticates the user and redirects to the chat portal if successful.
  - **Parameters**: `username`, `password`
  - **Response**: Redirects to `/portal` on success; raises `HTTPException` on failure.
- **POST `/creds/`**: Endpoint for user login, returning an access token.
  - **Parameters**: `OAuth2PasswordRequestForm`
  - **Response**: JSON containing the `access_token`.

### Chat Interactions
- **GET `/portal`**: Renders the chat portal page if the user is authenticated.
  - **Response**: HTML page (portal or login).
- **POST `/portal`**: Handles chat input and generates a response using the selected model.
  - **Parameters**: `user_input` (via form data).
  - **Response**: HTML page with the updated chat.
- **GET `/reports`**: Renders the reports page showing logs and responses.
  - **Response**: HTML page with logs.

### Configuration Management
- **GET `/config_id`**: Sets the configuration ID to be used by the user.
  - **Parameters**: `config_id`
  - **Response**: JSON confirming the configuration ID.

## Key Modules

### `api_client.py`
- **Purpose**: Manages API interactions, user authentication, token management, and interaction with various language models (e.g., OpenAI, Cohere, Anthropic).
- **Key Functions**:
  - `login(username: str, password: str)`: Authenticates a user and stores the access token.
  - `chat(user_input: str)`: Sends input to the language model and returns the response.
  - `chat_guard(user_input: str)`: Sends input to the Guard service and returns the response.
  - `set_config(config_id: str)`: Sets the configuration ID for the user.

### `user_data.py`
- **Purpose**: Manages user-specific data, including chat logs, responses, and configuration settings.
- **Key Classes**:
  - `UserData`: Stores data associated with each user.
  - `get_user_data(username: str) -> UserData`: Retrieves or creates the `UserData` for a specified user.

### `logger.py`
- **Purpose**: Manages logging of user interactions, storing them in user-specific log files.
- **Key Functions**:
  - `setup_logger(user: str)`: Sets up a logger for a specific user.
  - `log_interaction(...)`: Logs the interaction in CSV format seperated on a per date basis.

## Templates

### `home.html`
- **Purpose**: Renders the chat portal page where users can input text and view responses.
- **Key Elements**:
  - Form for user input.
  - Display of chat responses.

### `report.html`
- **Purpose**: Renders the reports page showing logs of user interactions and responses.
- **Key Elements**:
  - Display of chat logs.
  - Display of responses from the language models and guard service.

## Static Files
- **CSS**: Contains stylesheets for the frontend.
- **JavaScript**: Contains scripts for enhancing the frontend functionality.

## How It Works

### User Authentication:
- Users authenticate by sending their credentials to the `/login` endpoints. If successful, a JWT token is issued and used for subsequent requests.

### Chat Interaction:
- Authenticated users can access the chat portal where they can input text. The input is processed by a selected language model (e.g., OpenAI), and the response is displayed. Interaction logs are saved for future reference.

### Logging and Reports:
- All user interactions are logged, including the time taken for responses from both the language model and the guard service. Users can view these logs on the reports page.

### Configuration Management:
- Users can set and manage their configuration IDs, which determine which model or service is used during interactions.

## Security Considerations
- **JWT Authentication**: The application uses JWT for secure user authentication. Tokens are validated for each request to ensure that only authenticated users can access sensitive endpoints.
- **Environment Variables**: Sensitive information, such as the JWT secret key, is stored in environment variables to prevent exposure in the source code.
