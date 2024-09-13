
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

4. Run the application:
   ```bash
   uvicorn main:app --reload
   ```

## License
Please read the Tumeryk SaaS Evaluation Agreement
