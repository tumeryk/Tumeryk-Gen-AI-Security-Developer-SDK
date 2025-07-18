#!/usr/bin/env python3
"""
Local Fix for OAuth Template Issue

This script will fix the template path issue in your local auth.py file.
Run this script in your project root directory where main.py is located.
"""

import os
import pathlib
import shutil

def fix_auth_file():
    """Fix the auth.py file to use robust template path resolution."""
    
    auth_file = pathlib.Path("routers/auth.py")
    if not auth_file.exists():
        print("❌ Error: routers/auth.py not found. Make sure you're in the project root.")
        return False
    
    # Read the current auth.py content
    with open(auth_file, 'r') as f:
        content = f.read()
    
    # Check if it already has the fix
    if "get_templates_directory" in content:
        print("✅ Auth file already has the template fix!")
        return True
    
    # Create backup
    backup_file = auth_file.with_suffix('.py.backup')
    shutil.copy2(auth_file, backup_file)
    print(f"📁 Backup created: {backup_file}")
    
    # Find the templates line to replace
    lines = content.split('\n')
    
    # Find the router creation and templates initialization
    for i, line in enumerate(lines):
        if 'router = APIRouter()' in line:
            # Insert the template resolution function after the router creation
            template_code = '''
# Get templates directory - try multiple locations to ensure it works everywhere
import pathlib

def get_templates_directory():
    """Find the templates directory from multiple possible locations."""
    possible_paths = [
        # Relative to current file (normal case)
        pathlib.Path(__file__).parent.parent / "templates",
        # Relative to current working directory
        pathlib.Path.cwd() / "templates",
        # Direct path if we're already in project root
        pathlib.Path("templates"),
        # If running from a subdirectory
        pathlib.Path("../templates"),
    ]
    
    for path in possible_paths:
        if path.exists() and path.is_dir():
            # Verify it contains expected template files
            if (path / "login.html").exists():
                return str(path.resolve())
    
    # Fallback: create error message
    raise FileNotFoundError(
        f"Could not find templates directory. Searched in: {[str(p) for p in possible_paths]}"
    )

try:
    templates_dir = get_templates_directory()
    print(f"INFO: Using templates directory: {templates_dir}")
    templates = Jinja2Templates(directory=templates_dir)
except Exception as e:
    print(f"ERROR: Template resolution failed: {e}")
    # Fallback to original behavior
    templates = Jinja2Templates(directory="templates")
'''
            lines.insert(i + 1, template_code)
            break
    
    # Find and remove old templates line
    for i, line in enumerate(lines):
        if 'templates = Jinja2Templates(directory="templates")' in line:
            lines.pop(i)
            break
    
    # Write the fixed content
    with open(auth_file, 'w') as f:
        f.write('\n'.join(lines))
    
    print("✅ Auth file has been fixed with robust template resolution!")
    return True

def check_dependencies():
    """Check if OAuth dependencies are installed."""
    try:
        import authlib
        import httpx
        import cryptography
        print("✅ OAuth dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing OAuth dependencies: {e}")
        print("Run: pip install authlib httpx cryptography")
        return False

def main():
    print("🔧 OAuth Template Path Fix Tool")
    print("=" * 40)
    
    # Check current directory
    if not os.path.exists("main.py"):
        print("❌ Error: main.py not found. Please run this script from the project root directory.")
        return
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Fix auth file
    if fix_auth_file():
        print("\n🎉 Fix completed successfully!")
        print("\nNow try running your application:")
        print("python3 main.py")
    else:
        print("\n❌ Fix failed. Please check the error messages above.")

if __name__ == "__main__":
    main()