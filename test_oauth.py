#!/usr/bin/env python3
"""
OAuth Authentication Test Script

This script tests the OAuth authentication endpoints to ensure they're properly configured.
Run this after setting up your OAuth providers to verify everything is working.
"""

import requests
import sys
from urllib.parse import urlparse

def test_endpoint(url, expected_status=200, method='GET'):
    """Test an endpoint and return the result."""
    try:
        if method == 'GET':
            response = requests.get(url, allow_redirects=False)
        else:
            response = requests.post(url, allow_redirects=False)
        
        return {
            'url': url,
            'status': response.status_code,
            'success': response.status_code == expected_status,
            'headers': dict(response.headers),
            'content': response.text[:200] if response.text else None
        }
    except Exception as e:
        return {
            'url': url,
            'status': None,
            'success': False,
            'error': str(e)
        }

def test_oauth_setup(base_url='http://localhost:8500'):
    """Test OAuth setup and configuration."""
    print(f"Testing OAuth setup at {base_url}")
    print("=" * 50)
    
    # Test auth status endpoint
    print("\n1. Testing OAuth status endpoint...")
    status_result = test_endpoint(f"{base_url}/auth/status")
    if status_result['success']:
        print("✅ OAuth status endpoint is working")
        try:
            import json
            status_data = json.loads(status_result['content'])
            print(f"   Google configured: {status_data.get('google', False)}")
            print(f"   GitHub configured: {status_data.get('github', False)}")
            print(f"   Apple configured: {status_data.get('apple', False)}")
        except:
            print("   Could not parse status response")
    else:
        print(f"❌ OAuth status endpoint failed: {status_result.get('error', 'Unknown error')}")
    
    # Test OAuth initiation endpoints
    oauth_providers = [
        ('Google', f"{base_url}/auth/google"),
        ('GitHub', f"{base_url}/auth/github"),
        ('Apple', f"{base_url}/auth/apple")
    ]
    
    print("\n2. Testing OAuth initiation endpoints...")
    for provider, url in oauth_providers:
        result = test_endpoint(url, expected_status=302)  # Expect redirect
        if result['success']:
            print(f"✅ {provider} OAuth initiation is working")
            location = result['headers'].get('location', '')
            if location:
                parsed = urlparse(location)
                print(f"   Redirects to: {parsed.netloc}")
        else:
            if result['status'] == 500:
                print(f"⚠️  {provider} OAuth not configured (missing credentials)")
            else:
                print(f"❌ {provider} OAuth failed: Status {result['status']}")
    
    # Test main login page
    print("\n3. Testing main login page...")
    login_result = test_endpoint(f"{base_url}/")
    if login_result['success']:
        print("✅ Main login page is accessible")
        if 'Continue with Google' in login_result.get('content', ''):
            print("   OAuth buttons are present in login page")
        else:
            print("   OAuth buttons may not be visible (check configuration)")
    else:
        print(f"❌ Main login page failed: {login_result.get('error', 'Unknown error')}")
    
    # Test traditional login endpoint
    print("\n4. Testing traditional login endpoint...")
    creds_result = test_endpoint(f"{base_url}/creds/", expected_status=422, method='POST')
    if creds_result['status'] == 422:
        print("✅ Traditional login endpoint is working (422 expected without credentials)")
    else:
        print(f"❌ Traditional login endpoint unexpected response: {creds_result['status']}")

def main():
    """Main function to run tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test OAuth authentication setup')
    parser.add_argument('--url', default='http://localhost:8500', 
                       help='Base URL of the application (default: http://localhost:8500)')
    
    args = parser.parse_args()
    
    print("OAuth Authentication Test")
    print("=" * 30)
    print("This script tests your OAuth authentication setup.")
    print("Make sure your application is running before running this test.\n")
    
    test_oauth_setup(args.url)
    
    print("\n" + "=" * 50)
    print("Test completed!")
    print("\nNext steps:")
    print("1. If providers show as 'not configured', check your .env file")
    print("2. If redirects fail, verify your OAuth app settings")
    print("3. Test actual login flows in a web browser")
    print("4. Check the application logs for detailed error messages")

if __name__ == '__main__':
    main()