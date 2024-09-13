import time
from proxy_core.api_client import ApiClient
import os

def test_api_client():
    # Initialize the API client
    url = os.getenv("BASE_URL")
    username = os.getenv("USERNAME")
    password = os.getenv("PASSWORD")
    print(url,username,password)
    api_client = ApiClient(url)

    # Step 1: Login with your username and password
    login_response = api_client.login(username=username, password= password)
    print(api_client.base_url)
    print(
        "Login Response:", login_response
    )  # Check if login was successful# Step 2: Set the config ID to "hr_policy"
    set_config_response = api_client.set_config(config_id="hr_policy")
    print(
        "Set Config Response:", set_config_response
    )  # Check if config ID was set successfully# Step 3: Test the chat method to send a direct input to the LLM
    chat_message = "How do you implement a binary tree in Python?"
    start_time = time.time()
    chat_response = api_client.chat(chat_message)
    chat_response_time = time.time() - start_time
    print(
        "Chat Response:", chat_response
    )  # Print the response from the LLM# Step 4: Test the chat_guard method to send input to the GuardAI service
    guard_message = chat_message
    start_time = time.time()
    guard_response = api_client.chat_guard(guard_message)
    guard_response_time = time.time() - start_time
    print(
        "Guard Response:", guard_response
    )  # Print the response from the GuardAI service# Determine if there's a violation


def test_invalid_login(api_client):
    try:
        print("\nTesting invalid login credentials...")
        login_response = api_client.login(username="wrongUser", password="wrongPass")
        print("Invalid Login Response:", login_response)
    except Exception as e:
        print("Invalid login failed as expected:", e)


def test_invalid_config_id(api_client):
    try:
        print("\nTesting invalid config ID...")
        set_config_response = api_client.set_config(config_id="non_existent_config")
        print("Invalid Set Config Response:", set_config_response)
    except Exception as e:
        print("Invalid config ID set failed as expected:", e)


def test_invalid_chat_input():
    try:
        api_client = ApiClient()
        print("\nTesting chat without logging in")
        chat_message = ""
        start_time = time.time()
        chat_response = api_client.chat(chat_message)
        chat_response_time = time.time() - start_time
        print("Invalid Chat Response:", chat_response)
    except Exception as e:
        print("Invalid chat failed as expected:", e)


def test_invalid_chat_guard_input():
    try:
        api_client = ApiClient()
        print("\nTesting chat_guard")
        guard_message = None
        start_time = time.time()
        guard_response = api_client.chat_guard(guard_message)
        guard_response_time = time.time() - start_time
        print("Invalid Guard Response:", guard_response)
    except Exception as e:
        print("Invalid guard chat failed as expected:", e)


if __name__ == "__main__":
    # Create a single instance of ApiClient
    # api_client = ApiClient()

    # Run tests using the shared instance
    # test_invalid_login(api_client)
    # test_invalid_config_id(api_client)
    # test_invalid_chat_input()
    # test_invalid_chat_guard_input()
    test_api_client()
