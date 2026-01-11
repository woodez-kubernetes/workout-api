#!/usr/bin/env python
"""
Simplified authentication test that doesn't require MongoDB connection.
Tests PostgreSQL-based Django authentication only.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Disconnect MongoDB before Django setup to avoid connection errors
import mongoengine
mongoengine.disconnect()

django.setup()

from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token


def cleanup_test_users():
    """Clean up test users from previous runs."""
    User.objects.filter(username__startswith='testuser').delete()
    Token.objects.filter(user__username__startswith='testuser').delete()


def test_auth_flow():
    """Test complete authentication flow."""
    print("\n" + "="*60)
    print("AUTHENTICATION FLOW TEST")
    print("="*60)
    print("\nTesting PostgreSQL-based Django authentication...")

    client = APIClient()

    # Test 1: Registration
    print("\n1. Testing user registration...")
    response = client.post('/api/auth/register/', {
        'username': 'testuser1',
        'email': 'test@example.com',
        'password': 'SecurePass123!',
        'password_confirm': 'SecurePass123!',
        'first_name': 'Test',
        'last_name': 'User'
    }, format='json')

    if response.status_code == 201:
        token = response.data.get('token')
        print(f"   ✅ Registration successful")
        print(f"   - User ID: {response.data.get('user', {}).get('id')}")
        print(f"   - Username: {response.data.get('user', {}).get('username')}")
        print(f"   - Token: {token[:20]}...")
    else:
        print(f"   ❌ Registration failed: {response.status_code}")
        if hasattr(response, 'data'):
            print(f"      {response.data}")
        else:
            print(f"      {response.content}")
        return False

    # Test 2: Login
    print("\n2. Testing user login...")
    response = client.post('/api/auth/login/', {
        'username': 'testuser1',
        'password': 'SecurePass123!'
    }, format='json')

    if response.status_code == 200:
        login_token = response.data.get('token')
        print(f"   ✅ Login successful")
        print(f"   - Token: {login_token[:20]}...")
    else:
        print(f"   ❌ Login failed: {response.status_code}")
        return False

    # Test 3: Access protected endpoint
    print("\n3. Testing protected endpoint access...")
    client.credentials(HTTP_AUTHORIZATION=f'Token {login_token}')
    response = client.get('/api/auth/me/')

    if response.status_code == 200:
        print(f"   ✅ Protected endpoint accessible")
        print(f"   - Username: {response.data.get('user', {}).get('username')}")
        print(f"   - Email: {response.data.get('user', {}).get('email')}")
    else:
        print(f"   ❌ Protected endpoint failed: {response.status_code}")
        return False

    # Test 4: Update profile
    print("\n4. Testing profile update...")
    response = client.patch('/api/auth/profile/', {
        'first_name': 'Updated',
        'last_name': 'Name'
    }, format='json')

    if response.status_code == 200:
        print(f"   ✅ Profile updated")
        print(f"   - Name: {response.data.get('user', {}).get('first_name')} {response.data.get('user', {}).get('last_name')}")
    else:
        print(f"   ❌ Profile update failed: {response.status_code}")
        return False

    # Test 5: Change password
    print("\n5. Testing password change...")
    response = client.post('/api/auth/change-password/', {
        'old_password': 'SecurePass123!',
        'new_password': 'NewPass456!',
        'new_password_confirm': 'NewPass456!'
    }, format='json')

    if response.status_code == 200:
        new_token = response.data.get('token')
        print(f"   ✅ Password changed")
        print(f"   - New token: {new_token[:20]}...")
    else:
        print(f"   ❌ Password change failed: {response.status_code}")
        return False

    # Test 6: Logout
    print("\n6. Testing logout...")
    client.credentials(HTTP_AUTHORIZATION=f'Token {new_token}')
    response = client.post('/api/auth/logout/')

    if response.status_code == 200:
        print(f"   ✅ Logout successful")
    else:
        print(f"   ❌ Logout failed: {response.status_code}")
        return False

    # Test 7: Verify token is invalid
    print("\n7. Testing invalidated token...")
    response = client.get('/api/auth/me/')

    if response.status_code == 401:
        print(f"   ✅ Token correctly invalidated")
    else:
        print(f"   ❌ Token should be invalid: {response.status_code}")
        return False

    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    print("\nAuthentication system is working correctly!")
    print("\nNext steps:")
    print("1. Fix MongoDB authentication credentials to enable UserProfile creation")
    print("2. Test with MongoDB to verify profile data storage")
    print("3. Ready for Stage 6: Kubernetes Deployment")

    return True


def main():
    """Run authentication tests."""
    print("\nNote: MongoDB connection disabled for this test")
    print("      Testing Django/PostgreSQL authentication only\n")

    # Clean up from previous runs
    print("Cleaning up test users from previous runs...")
    cleanup_test_users()

    # Run tests
    success = test_auth_flow()

    # Clean up
    print("\nCleaning up test users...")
    cleanup_test_users()

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
