#!/usr/bin/env python3
"""
Fix Requirements for OAuth

This script ensures all OAuth dependencies are in requirements.txt
"""

import os

def fix_requirements():
    """Add OAuth dependencies to requirements.txt if missing."""
    
    oauth_deps = [
        "authlib",
        "httpx", 
        "cryptography"
    ]
    
    requirements_file = "requirements.txt"
    
    # Read existing requirements
    existing_reqs = set()
    if os.path.exists(requirements_file):
        with open(requirements_file, 'r') as f:
            existing_reqs = {line.strip().lower() for line in f if line.strip() and not line.startswith('#')}
    
    # Check what's missing
    missing_deps = []
    for dep in oauth_deps:
        if dep not in existing_reqs:
            missing_deps.append(dep)
    
    if not missing_deps:
        print("✅ All OAuth dependencies are already in requirements.txt")
        return True
    
    # Add missing dependencies
    print(f"📝 Adding missing OAuth dependencies: {missing_deps}")
    
    with open(requirements_file, 'a') as f:
        for dep in missing_deps:
            f.write(f"\n{dep}")
    
    print("✅ Requirements.txt updated successfully!")
    return True

if __name__ == "__main__":
    fix_requirements()