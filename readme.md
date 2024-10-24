# Tumeryk Gen AI Security Developer SDK Demo App

## Overview
The Tumeryk Gen AI Security Developer SDK Demo App showcases secure interaction with LLMs through:
1. LLM interactions 
2. Guardrails via the `tumeryk_guardrails` package

## UI Features

### Portal Interface
- LLM interactions 
- Policy selection for different guardrails rules

### Reports Page
- Interaction logs
- Response times for both LLM and guard
- Token usage statistics
- Violation tracking

## Setup Instructions

### Option 1: Using the Shell Script

1. Download `Run_Tumeryk_Proxy.sh`
2. Open terminal and navigate to the script location
3. Give execution permissions:
   ```bash
   chmod a+x Run_Tumeryk_Proxy.sh
   ```
4. Run the script:
   ```bash
   ./Run_Tumeryk_Proxy.sh
   ```

The script will automatically:
- Set up the environment
- Install dependencies
- Launch the FastAPI server

### Option 2: Manual Setup

1. Prerequisites:
   - Python 3.8+
   - `pip` package manager

2. Clone the repository:
   ```bash
   git clone https://github.com/tumeryk/Tumeryk-Gen-AI-Security-Developer-SDK.git
   cd Tumeryk-Gen-AI-Security-Developer-SDK
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   - Create a `.env` file in the project root
   - Add your environment variables:
     ```
     TUMERYK_USERNAME=your_username
     TUMERYK_PASSWORD=your_password
     TUMERYK_POLICY=your_policy
     TUMERYK_BASE_URL=https://chat.tmryk.com
     ```

5. Request access to Tumeryk:
   - Sign up at https://tumeryk.com/sign-up to create your credentials

6. Run the application:
   ```bash
   uvicorn main:app --reload
   ```

7. Access the web interface at `http://localhost:8000`

## Using the Demo App

1. **Login**
   - Use your Tumeryk credentials to log in
   - The system will authenticate with Tumeryk services

2. **Interface**
   - Select a policy from the dropdown menu
   - Enter your message in the chat input

3. **Reports**
   - View interaction logs
   - View response times
   - View token usage statistics
   - View security violations

