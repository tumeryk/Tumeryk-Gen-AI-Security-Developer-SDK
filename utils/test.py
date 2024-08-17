# Import the ApiClient class from your module
from api_client import ApiClient
from logger import *

import time
from api_client import ApiClient
from logger import log_interaction

def test_api_client():
    # Initialize the API client
    api_client = ApiClient()

    # Retrieve the model name from the ApiClient

    # Step 1: Login with your username and password
    login_response = api_client.login(username="nirmitCliente", password="abc123")
    print("Login Response:", login_response)  # Check if login was successful# Step 2: Set the config ID to "hr_policy"
    set_config_response = api_client.set_config(config_id="hr_policy")
    print("Set Config Response:", set_config_response)  # Check if config ID was set successfully# Step 3: Test the chat method to send a direct input to the LLM
    chat_message = "What is the weather like today?"
    start_time = time.time()
    chat_response = api_client.chat(chat_message)
    chat_response_time = time.time() - start_time
    print("Chat Response:", chat_response)  # Print the response from the LLM# Step 4: Test the chat_guard method to send input to the GuardAI service
    guard_message = "What is the weather like today?"
    start_time = time.time()
    guard_response = api_client.chat_guard(guard_message)
    guard_response_time = time.time() - start_time
    print("Guard Response:", guard_response)  # Print the response from the GuardAI service# Determine if there's a violation
    violation = False
    model_name = api_client.user_data.models["hr_policy"]["model_name"]
    if guard_response == "Sorry, I can't assist with that.":
        violation = True# Log the interaction
    log_interaction(
        user="nirmitCliente",
        role="user",
        message=chat_message,
        bot_response_time=chat_response_time,
        guard_response_time=guard_response_time,
        model=model_name,  # Use the actual model name from ApiClient
        config_id="hr_policy",
        bot_response=chat_response,
        guard_response=guard_response,
        violation=violation
    )

if __name__ == "__main__":
    test_api_client()
