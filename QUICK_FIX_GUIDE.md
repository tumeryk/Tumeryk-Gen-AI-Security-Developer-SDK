# 🚨 QUICK FIX for OAuth Template Error

## Problem
You're getting this error:
```
jinja2.exceptions.TemplateNotFound: 'login.html' not found in search path: 'templates'
```

## Root Cause
Your `Run_Tumeryk_Proxy.sh` script clones a fresh repository that doesn't have the OAuth authentication changes, and the template path is hardcoded.

## 🔧 SOLUTION (Choose One)

### Option 1: Quick Fix (Recommended)
Run these commands in your project directory where `main.py` is located:

```bash
# 1. Download and run the fix script
curl -o local_fix.py https://raw.githubusercontent.com/your-repo/local_fix.py
python3 local_fix.py

# 2. Install OAuth dependencies
pip install authlib httpx cryptography

# 3. Run your application
python3 main.py
```

### Option 2: Manual Fix
1. **Stop any running server** first:
   ```bash
   pkill -f "python.*main.py"
   ```

2. **Install OAuth dependencies**:
   ```bash
   pip install authlib httpx cryptography
   ```

3. **Fix the auth.py file manually**:
   Open `routers/auth.py` and find this line (around line 30):
   ```python
   templates = Jinja2Templates(directory="templates")
   ```
   
   Replace it with:
   ```python
   # Get templates directory - robust path resolution
   import pathlib
   
   def get_templates_directory():
       """Find templates directory from multiple possible locations."""
       possible_paths = [
           pathlib.Path(__file__).parent.parent / "templates",
           pathlib.Path.cwd() / "templates", 
           pathlib.Path("templates"),
           pathlib.Path("../templates"),
       ]
       
       for path in possible_paths:
           if path.exists() and path.is_dir():
               if (path / "login.html").exists():
                   return str(path.resolve())
       
       raise FileNotFoundError(f"Templates not found in: {[str(p) for p in possible_paths]}")
   
   try:
       templates_dir = get_templates_directory()
       print(f"INFO: Using templates directory: {templates_dir}")
       templates = Jinja2Templates(directory=templates_dir)
   except Exception as e:
       print(f"ERROR: {e}")
       templates = Jinja2Templates(directory="templates")  # fallback
   ```

4. **Run the application**:
   ```bash
   python3 main.py
   ```

### Option 3: Script Modification
Modify your `Run_Tumeryk_Proxy.sh` script to not clone fresh every time:

1. **Edit `Run_Tumeryk_Proxy.sh`**:
   Comment out or remove these lines:
   ```bash
   # rm -rf Tumeryk-Gen-AI-Security-Developer-SDK
   # git clone https://github.com/your-repo/Tumeryk-Gen-AI-Security-Developer-SDK.git
   ```

2. **Add OAuth dependencies** to the script:
   After the existing pip install, add:
   ```bash
   pip install authlib httpx cryptography
   ```

## 🧪 Test the Fix

After applying any option above, test it:

```bash
# Test 1: Check if app starts
python3 -c "from main import app; print('✅ App imports successfully')"

# Test 2: Test the root endpoint  
python3 -c "
from fastapi.testclient import TestClient
from main import app
client = TestClient(app)
response = client.get('/')
print(f'Status: {response.status_code}')
print('✅ SUCCESS!' if response.status_code == 200 else '❌ Still failing')
"

# Test 3: Start the server
python3 main.py
```

## 🎯 Expected Result

You should see:
```
INFO: Using templates directory: /path/to/your/templates
INFO: Started server process [XXXX]
INFO: Uvicorn running on http://0.0.0.0:8500
```

And visiting `http://localhost:8500` should show the login page with OAuth buttons.

## 📞 If Still Having Issues

1. **Check your working directory**: Make sure you're in the directory with `main.py`
2. **Check templates exist**: Run `ls templates/` and verify `login.html` exists
3. **Verify dependencies**: Run `pip list | grep -E "(authlib|httpx|cryptography)"`
4. **Check Python version**: Ensure you're using Python 3.7+

## 🔐 OAuth Configuration

After fixing the template issue, configure OAuth providers by:

1. **Copy environment template**: `cp .env.example .env`
2. **Add your OAuth credentials** to `.env`
3. **See `OAUTH_SETUP.md`** for detailed provider setup instructions

---
**This fix resolves the template path issue permanently and adds full OAuth support!**