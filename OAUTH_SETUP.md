# OAuth Authentication Setup Guide

This guide will walk you through setting up OAuth authentication for Google, Apple, and GitHub in your FastAPI application.

## Prerequisites

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Copy the environment template:
```bash
cp .env.example .env
```

## 1. Google OAuth Setup

### Step 1: Create a Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API or Google Identity API

### Step 2: Create OAuth Credentials
1. Navigate to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Configure the consent screen if prompted
4. Select "Web application" as the application type
5. Add authorized redirect URIs:
   - `http://localhost:8500/auth/google/callback` (for development)
   - `https://yourdomain.com/auth/google/callback` (for production)

### Step 3: Configure Environment Variables
Add to your `.env` file:
```env
GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

## 2. GitHub OAuth Setup

### Step 1: Create a GitHub OAuth App
1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Click "New OAuth App"
3. Fill in the application details:
   - **Application name**: Your app name
   - **Homepage URL**: `http://localhost:8500` (for development)
   - **Authorization callback URL**: `http://localhost:8500/auth/github/callback`

### Step 2: Configure Environment Variables
Add to your `.env` file:
```env
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
```

## 3. Apple Sign In Setup

### Step 1: Apple Developer Account Requirements
- You need an Apple Developer account ($99/year)
- Access to Apple Developer Console

### Step 2: Create an App ID
1. Go to [Apple Developer Console](https://developer.apple.com/account/)
2. Navigate to "Certificates, Identifiers & Profiles"
3. Create a new App ID with "Sign In with Apple" capability

### Step 3: Create a Services ID
1. Create a new Services ID (this will be your client ID)
2. Configure "Sign In with Apple" for this Services ID
3. Add your domain and return URLs:
   - Domain: `localhost` (for development) or your domain
   - Return URLs: `http://localhost:8500/auth/apple/callback`

### Step 4: Create a Private Key
1. Go to "Keys" section in Apple Developer Console
2. Create a new key with "Sign In with Apple" capability
3. Download the `.p8` file (you can only download it once!)
4. Note the Key ID

### Step 5: Configure Environment Variables
Add to your `.env` file:
```env
APPLE_CLIENT_ID=your.service.identifier
APPLE_TEAM_ID=YOUR_TEAM_ID
APPLE_KEY_ID=YOUR_KEY_ID
APPLE_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----
YOUR_PRIVATE_KEY_CONTENT_HERE
-----END PRIVATE KEY-----
```

**Note**: You can also base64 encode the private key and store it as a single line:
```env
APPLE_PRIVATE_KEY=LS0tLS1CRUdJTi...  # base64 encoded key
```

## 4. General Configuration

### Base URL Configuration
Set your application's base URL in the `.env` file:
```env
REDIRECT_URI_BASE=http://localhost:8500  # for development
# REDIRECT_URI_BASE=https://yourdomain.com  # for production
```

### JWT Secret Key
Generate a strong JWT secret key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Add it to your `.env` file:
```env
JWT_SECRET_KEY=your_generated_secret_key
```

## 5. Testing Your Setup

### Start the Application
```bash
python main.py
```

### Test OAuth Providers
1. Navigate to `http://localhost:8500`
2. You should see OAuth login buttons for configured providers
3. Click on each provider to test the authentication flow
4. Check `/auth/status` endpoint to see which providers are configured

### Common Issues and Solutions

#### Google OAuth Issues
- **Invalid redirect URI**: Ensure the redirect URI in Google Console matches exactly
- **Consent screen not configured**: Complete the OAuth consent screen setup

#### GitHub OAuth Issues
- **Invalid callback URL**: Verify the callback URL in GitHub app settings
- **Private email**: The app handles private GitHub emails automatically

#### Apple Sign In Issues
- **Invalid client**: Ensure the Services ID is correctly configured
- **Key issues**: Verify the private key format and Key ID
- **Domain verification**: Make sure your domain is verified in Apple Developer Console

#### General Issues
- **Missing dependencies**: Run `pip install -r requirements.txt`
- **Environment variables**: Ensure all required variables are set in `.env`
- **Port conflicts**: Change the port in `main.py` if 8500 is in use

## 6. Security Considerations

### Production Deployment
1. **Use HTTPS**: Always use HTTPS in production
2. **Update redirect URIs**: Update all OAuth apps with production URLs
3. **Secure cookies**: The app sets secure cookies in production
4. **Environment variables**: Use secure environment variable management
5. **JWT secret**: Use a strong, unique JWT secret key

### CSRF Protection
The implementation includes CSRF protection through:
- State parameter validation
- Secure cookie handling
- HttpOnly cookies for sensitive data

## 7. API Endpoints

### OAuth Initiation
- `GET /auth/google` - Start Google OAuth flow
- `GET /auth/github` - Start GitHub OAuth flow  
- `GET /auth/apple` - Start Apple OAuth flow

### OAuth Callbacks
- `GET /auth/google/callback` - Google OAuth callback
- `GET /auth/github/callback` - GitHub OAuth callback
- `POST /auth/apple/callback` - Apple OAuth callback (POST for Apple)

### Utility Endpoints
- `GET /auth/status` - Check which OAuth providers are configured
- `POST /login` - Traditional username/password login
- `POST /creds/` - API token login

## 8. User Data Handling

After successful OAuth authentication, the user's data is stored in the JWT token with the following structure:

```json
{
  "sub": "user@example.com",
  "provider": "google|github|apple",
  "name": "User Name",
  "picture": "https://...",  // Google
  "avatar": "https://...",   // GitHub
  "github_id": 12345,        // GitHub
  "apple_id": "...",         // Apple
  "exp": 1234567890
}
```

This data can be accessed in your application through the existing user authentication system.

## 9. Customization

### Adding More Providers
To add additional OAuth providers:
1. Add the provider configuration to the environment variables
2. Create new routes following the existing pattern
3. Update the login template with new buttons
4. Add the provider to the `/auth/status` endpoint

### Styling
Customize the OAuth buttons by modifying the CSS in `templates/login.html`.

### User Data Processing
Modify the user data processing in each OAuth callback to store additional information as needed.

## Support

For issues or questions:
1. Check the FastAPI logs for detailed error messages
2. Verify all environment variables are correctly set
3. Ensure OAuth app configurations match your application URLs
4. Test with different browsers to rule out cookie/session issues

Happy authenticating! 🔐