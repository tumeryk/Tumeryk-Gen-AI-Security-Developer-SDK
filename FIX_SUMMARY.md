# OAuth Authentication - Template Path Fix

## Issue
The application was throwing a 500 Internal Server Error with the message:
```
jinja2.exceptions.TemplateNotFound: 'login.html' not found in search path: 'templates'
```

## Root Cause
The `templates` directory path was hardcoded as `"templates"` which only works when the application is run from the project root directory. When running from a different working directory, Jinja2 couldn't find the templates.

## Solution Applied
Implemented a robust template directory resolution system that:

1. **Tries multiple possible paths** in order:
   - Relative to the current file location (normal case)
   - Relative to current working directory
   - Direct path if already in project root
   - Parent directory if running from subdirectory

2. **Validates each path** by checking:
   - Directory exists
   - Contains expected template files (e.g., `login.html`)

3. **Provides clear error messages** if templates cannot be found

## Code Changes
Updated `routers/auth.py` with the `get_templates_directory()` function that intelligently finds the templates regardless of working directory.

## Result
✅ **Application now works from any directory**
✅ **Root endpoint returns 200 status**
✅ **OAuth authentication endpoints ready**

## Testing
Run from any directory:
```bash
python3 main.py
```

The application will automatically find and use the correct templates directory.