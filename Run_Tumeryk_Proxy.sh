
# Step 1: Clone the Repository (if it doesn't exist)
# ==================================================
# Define the repository name and directory
REPO_NAME="Tumeryk-Gen-AI-Security-Developer-SDK"
REPO_URL="https://github.com/tumeryk/Tumeryk-Gen-AI-Security-Developer-SDK.git"

# Check if the repository directory already exists
if [ ! -d "$REPO_NAME" ]; then
  # Clone the repository from GitHub
  git clone $REPO_URL || { echo 'Failed to clone the repository. Please check your internet connection or the repository URL.'; exit 1; }
fi

# Navigate into the cloned directory
cd $REPO_NAME || { echo 'Failed to enter the project directory. Please check if the repository was cloned correctly.'; exit 1; }

# Step 2: Create a Virtual Environment and Install Dependencies
# ============================================================

# Create virtual environment (if it doesn't already exist)
if [ ! -d "env" ]; then
  python3 -m venv env
fi

# Ensure virtual environment directory permissions
chmod -R 755 env

# Activate virtual environment
source env/bin/activate || { echo 'Failed to activate virtual environment. Please check if the venv directory exists.'; exit 1; }

# Install dependencies from requirements.txt
if [ -f "requirements.txt" ]; then
  pip install -r requirements.txt || { echo 'Failed to install dependencies. Please check the requirements.txt file.'; exit 1; }
else
  echo 'requirements.txt not found. Please provide a valid requirements file.'
  exit 1
fi

# Freeze the installed dependencies (to make sure they're all captured)
pip freeze > pip_freeze.txt

# Step 3: Start the FastAPI Application
# =====================================

# Start the FastAPI application using uvicorn on port 8500
uvicorn main:app --host 0.0.0.0 --port 8500 &

# Give the server a few seconds to start up
sleep 5

# Step 4: Open the Application in the Default Web Browser
# =======================================================

# Open the FastAPI application in the default web browser
if command -v xdg-open > /dev/null; then
  xdg-open http://0.0.0.0:8500
elif command -v open > /dev/null; then
  open http://0.0.0.0:8500
else
  echo "Please open http://0.0.0.0:8500 in your web browser."
fi

# ==========================
# After running this script, the server will start automatically and be available at http://0.0.0.0:8500