#!/usr/bin/env python3
"""
Complete Mac Fix Script for OAuth Template Error

This script will:
1. Install all required dependencies 
2. Fix the template path issue
3. Test the application
4. Provide next steps

Run this in your project directory where main.py is located.
"""

import subprocess
import sys
import pathlib
import shutil
import os

def run_command(cmd, description=""):
    """Run a command and return success status."""
    print(f"🔄 {description}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            return True
        else:
            print(f"❌ {description} - FAILED: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

def install_dependencies():
    """Install all required dependencies."""
    print("\n📦 INSTALLING DEPENDENCIES")
    print("=" * 40)
    
    dependencies = [
        "fastapi",
        "uvicorn", 
        "requests",
        "aiofiles",
        "jinja2",
        "PyJWT",
        "python-multipart", 
        "python-dotenv",
        "tumeryk_guardrails",
        "litellm",
        "pyyaml",
        "authlib",
        "httpx", 
        "cryptography"
    ]
    
    for dep in dependencies:
        success = run_command(f"pip install {dep}", f"Installing {dep}")
        if not success:
            print(f"⚠️  Warning: Failed to install {dep}")
    
    return True

def fix_auth_file():
    """Fix the auth.py file template path issue."""
    print("\n🔧 FIXING TEMPLATE PATH ISSUE")
    print("=" * 40)
    
    auth_file = pathlib.Path("routers/auth.py")
    if not auth_file.exists():
        print("❌ routers/auth.py not found. Make sure you're in the project root.")
        return False
    
    # Read current content
    with open(auth_file, 'r') as f:
        content = f.read()
    
    # Check if already fixed
    if 'get_templates_directory' in content:
        print("✅ Template fix already applied!")
        return True
    
    # Create backup
    backup_file = auth_file.with_suffix('.py.backup')
    shutil.copy2(auth_file, backup_file)
    print(f"📁 Backup created: {backup_file}")
    
    # Apply the fix
    template_fix = '''# Get templates directory - robust path resolution
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
    print(f"ERROR: Template resolution failed: {e}")
    templates = Jinja2Templates(directory="templates")  # fallback'''
    
    # Replace the hardcoded templates line
    if 'templates = Jinja2Templates(directory="templates")' in content:
        content = content.replace(
            'templates = Jinja2Templates(directory="templates")',
            template_fix
        )
        
        with open(auth_file, 'w') as f:
            f.write(content)
        
        print("✅ Template fix applied successfully!")
        return True
    else:
        print("⚠️  Could not find the templates line to replace")
        return False

def test_application():
    """Test if the application can start."""
    print("\n🧪 TESTING APPLICATION")
    print("=" * 40)
    
    test_script = '''
try:
    from fastapi.testclient import TestClient
    from main import app
    client = TestClient(app)
    response = client.get("/")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ SUCCESS: Application is working!")
        exit(0)
    else:
        print(f"❌ FAILED: Got status {response.status_code}")
        exit(1)
except Exception as e:
    print(f"❌ ERROR: {e}")
    exit(1)
'''
    
    with open("test_app.py", "w") as f:
        f.write(test_script)
    
    success = run_command("python3 test_app.py", "Testing application startup")
    
    # Clean up test file
    if os.path.exists("test_app.py"):
        os.remove("test_app.py")
    
    return success

def main():
    print("🎯 MAC OAUTH FIX SCRIPT")
    print("=" * 50)
    print("This will fix your OAuth template error completely!")
    print()
    
    # Check if we're in the right directory
    if not os.path.exists("main.py"):
        print("❌ ERROR: main.py not found!")
        print("Please run this script from your project root directory:")
        print("cd /Users/rvalia/Tumeryk-Gen-AI-Security-Developer-SDK")
        return
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ ERROR: Python 3.7+ required")
        return
    
    print(f"✅ Python {sys.version}")
    print(f"✅ Working directory: {os.getcwd()}")
    
    # Step 1: Install dependencies
    if not install_dependencies():
        print("⚠️  Some dependencies failed to install, continuing anyway...")
    
    # Step 2: Fix auth file
    if not fix_auth_file():
        print("❌ Failed to fix auth file")
        return
    
    # Step 3: Test application
    if test_application():
        print("\n🎉 SUCCESS! Your application is now working!")
        print("\n📋 NEXT STEPS:")
        print("1. Start your application: python3 main.py")
        print("2. Visit: http://localhost:8500")
        print("3. Configure OAuth: cp .env.example .env")
        print("4. See OAUTH_SETUP.md for provider setup")
    else:
        print("\n❌ Application test failed. Check the errors above.")
        print("\nTry running manually:")
        print("python3 main.py")

if __name__ == "__main__":
    main()