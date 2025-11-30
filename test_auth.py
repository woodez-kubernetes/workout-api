#!/usr/bin/env python
"""
Test script to verify authentication endpoints are configured correctly.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from workouts.models import UserProfile


def cleanup_test_users():
    """Clean up test users from previous runs."""
    User.objects.filter(username__startswith='testuser').delete()
    UserProfile.objects.filter(username__startswith='testuser').delete()


def test_auth_urls():
    """Test that authentication URLs are configured."""
    print("\n" + "="*60)
    print("Testing Authentication URL Configuration")
    print("="*60)

    auth_urls = [
        ('auth-register', 'POST /api/auth/register/'),
        ('auth-login', 'POST /api/auth/login/'),
        ('auth-logout', 'POST /api/auth/logout/'),
        ('auth-me', 'GET /api/auth/me/'),
        ('auth-update-profile', 'PUT /api/auth/profile/'),
        ('auth-change-password', 'POST /api/auth/change-password/'),
    ]

    all_pass = True
    for url_name, description in auth_urls:
        try:
            path = reverse(url_name)
            print(f"  ✓ {description} -> {path}")
        except Exception as e:
            print(f"  ❌ {description} -> Failed: {e}")
            all_pass = False

    if all_pass:
        print("\n✅ All authentication URLs configured correctly!")
    return all_pass


def test_registration():
    """Test user registration endpoint."""
    print("\n" + "="*60)
    print("Testing User Registration")
    print("="*60)

    client = APIClient()

    # Test successful registration
    print("\n1. Testing successful registration...")
    response = client.post('/api/auth/register/', {
        'username': 'testuser1',
        'email': 'test1@example.com',
        'password': 'SecurePass123!',
        'password_confirm': 'SecurePass123!',
        'first_name': 'Test',
        'last_name': 'User',
        'height': 180,
        'weight': 75.5,
        'fitness_goal': 'strength'
    }, format='json')

    if response.status_code == 201:
        print("   ✓ User registered successfully")
        print(f"   ✓ Token received: {response.data.get('token')[:20]}...")
        print(f"   ✓ User ID: {response.data.get('user', {}).get('id')}")
        print(f"   ✓ Profile created: {response.data.get('profile', {}).get('id')}")
    else:
        print(f"   ❌ Registration failed: {response.status_code}")
        print(f"      {response.data}")
        return False

    # Test duplicate username
    print("\n2. Testing duplicate username...")
    response = client.post('/api/auth/register/', {
        'username': 'testuser1',
        'email': 'different@example.com',
        'password': 'SecurePass123!',
        'password_confirm': 'SecurePass123!'
    }, format='json')

    if response.status_code == 400 and 'already exists' in str(response.data.get('error', '')).lower():
        print("   ✓ Duplicate username rejected correctly")
    else:
        print(f"   ❌ Should reject duplicate username: {response.status_code}")
        return False

    # Test password mismatch
    print("\n3. Testing password mismatch...")
    response = client.post('/api/auth/register/', {
        'username': 'testuser2',
        'email': 'test2@example.com',
        'password': 'SecurePass123!',
        'password_confirm': 'DifferentPass123!'
    }, format='json')

    if response.status_code == 400 and 'do not match' in str(response.data.get('error', '')).lower():
        print("   ✓ Password mismatch rejected correctly")
    else:
        print(f"   ❌ Should reject password mismatch: {response.status_code}")
        return False

    print("\n✅ Registration endpoint working correctly!")
    return True


def test_login():
    """Test user login endpoint."""
    print("\n" + "="*60)
    print("Testing User Login")
    print("="*60)

    client = APIClient()

    # Test successful login
    print("\n1. Testing successful login...")
    response = client.post('/api/auth/login/', {
        'username': 'testuser1',
        'password': 'SecurePass123!'
    }, format='json')

    if response.status_code == 200:
        token = response.data.get('token')
        print("   ✓ Login successful")
        print(f"   ✓ Token received: {token[:20]}...")
        print(f"   ✓ User: {response.data.get('user', {}).get('username')}")
    else:
        print(f"   ❌ Login failed: {response.status_code}")
        print(f"      {response.data}")
        return False, None

    # Test invalid credentials
    print("\n2. Testing invalid credentials...")
    response = client.post('/api/auth/login/', {
        'username': 'testuser1',
        'password': 'WrongPassword!'
    }, format='json')

    if response.status_code == 401:
        print("   ✓ Invalid credentials rejected correctly")
    else:
        print(f"   ❌ Should reject invalid credentials: {response.status_code}")
        return False, None

    print("\n✅ Login endpoint working correctly!")
    return True, token


def test_protected_endpoints(token):
    """Test protected endpoints with authentication."""
    print("\n" + "="*60)
    print("Testing Protected Endpoints")
    print("="*60)

    client = APIClient()

    # Test /auth/me/ without token
    print("\n1. Testing /auth/me/ without token...")
    response = client.get('/api/auth/me/')
    if response.status_code == 401:
        print("   ✓ Correctly rejected unauthenticated request")
    else:
        print(f"   ❌ Should reject unauthenticated request: {response.status_code}")
        return False

    # Test /auth/me/ with token
    print("\n2. Testing /auth/me/ with token...")
    client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
    response = client.get('/api/auth/me/')

    if response.status_code == 200:
        print("   ✓ Authenticated request successful")
        print(f"   ✓ User: {response.data.get('user', {}).get('username')}")
        print(f"   ✓ Profile: {response.data.get('profile', {}).get('id')}")
    else:
        print(f"   ❌ Authenticated request failed: {response.status_code}")
        return False

    print("\n✅ Protected endpoints working correctly!")
    return True


def test_profile_update(token):
    """Test profile update endpoint."""
    print("\n" + "="*60)
    print("Testing Profile Update")
    print("="*60)

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

    print("\n1. Testing profile update...")
    response = client.patch('/api/auth/profile/', {
        'first_name': 'Updated',
        'height': 185,
        'weight': 80.0,
        'fitness_goal': 'cardio'
    }, format='json')

    if response.status_code == 200:
        print("   ✓ Profile updated successfully")
        print(f"   ✓ First name: {response.data.get('user', {}).get('first_name')}")
        print(f"   ✓ Height: {response.data.get('profile', {}).get('height')}")
        print(f"   ✓ Fitness goal: {response.data.get('profile', {}).get('fitness_goal')}")
    else:
        print(f"   ❌ Profile update failed: {response.status_code}")
        print(f"      {response.data}")
        return False

    print("\n✅ Profile update working correctly!")
    return True


def test_password_change(token):
    """Test password change endpoint."""
    print("\n" + "="*60)
    print("Testing Password Change")
    print("="*60)

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

    # Test with wrong old password
    print("\n1. Testing with wrong old password...")
    response = client.post('/api/auth/change-password/', {
        'old_password': 'WrongPassword!',
        'new_password': 'NewSecurePass123!',
        'new_password_confirm': 'NewSecurePass123!'
    }, format='json')

    if response.status_code == 400 and 'incorrect' in str(response.data.get('error', '')).lower():
        print("   ✓ Wrong old password rejected correctly")
    else:
        print(f"   ❌ Should reject wrong old password: {response.status_code}")
        return False

    # Test successful password change
    print("\n2. Testing successful password change...")
    response = client.post('/api/auth/change-password/', {
        'old_password': 'SecurePass123!',
        'new_password': 'NewSecurePass123!',
        'new_password_confirm': 'NewSecurePass123!'
    }, format='json')

    if response.status_code == 200:
        new_token = response.data.get('token')
        print("   ✓ Password changed successfully")
        print(f"   ✓ New token received: {new_token[:20]}...")
    else:
        print(f"   ❌ Password change failed: {response.status_code}")
        print(f"      {response.data}")
        return False

    # Test login with new password
    print("\n3. Testing login with new password...")
    client = APIClient()  # Reset client
    response = client.post('/api/auth/login/', {
        'username': 'testuser1',
        'password': 'NewSecurePass123!'
    }, format='json')

    if response.status_code == 200:
        print("   ✓ Login with new password successful")
    else:
        print(f"   ❌ Login with new password failed: {response.status_code}")
        return False

    print("\n✅ Password change working correctly!")
    return True, new_token


def test_logout(token):
    """Test logout endpoint."""
    print("\n" + "="*60)
    print("Testing Logout")
    print("="*60)

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

    print("\n1. Testing logout...")
    response = client.post('/api/auth/logout/')

    if response.status_code == 200:
        print("   ✓ Logout successful")
    else:
        print(f"   ❌ Logout failed: {response.status_code}")
        return False

    # Test that token is no longer valid
    print("\n2. Testing invalidated token...")
    response = client.get('/api/auth/me/')

    if response.status_code == 401:
        print("   ✓ Token correctly invalidated")
    else:
        print(f"   ❌ Token should be invalid: {response.status_code}")
        return False

    print("\n✅ Logout working correctly!")
    return True


def main():
    """Run all authentication tests."""
    print("\n" + "="*60)
    print("AUTHENTICATION ENDPOINT TESTING")
    print("="*60)
    print("\nNote: These tests require a working Django setup but NOT MongoDB")
    print("      User data will be stored in Django's default database")

    # Clean up from previous runs
    print("\nCleaning up test users from previous runs...")
    cleanup_test_users()

    results = []

    # Run tests
    results.append(("URL Configuration", test_auth_urls()))

    if results[0][1]:  # Only continue if URLs are configured
        results.append(("Registration", test_registration()))

        login_result, token = test_login()
        results.append(("Login", login_result))

        if token:
            results.append(("Protected Endpoints", test_protected_endpoints(token)))
            results.append(("Profile Update", test_profile_update(token)))

            password_result, new_token = test_password_change(token)
            results.append(("Password Change", password_result))

            if new_token:
                results.append(("Logout", test_logout(new_token)))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status_icon = "✅ PASS" if result else "❌ FAIL"
        print(f"{status_icon} - {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    # Clean up
    print("\nCleaning up test users...")
    cleanup_test_users()

    if passed == total:
        print("\n🎉 All authentication endpoints working correctly!")
        print("\nAuthentication Flow:")
        print("1. Register: POST /api/auth/register/")
        print("2. Login: POST /api/auth/login/ (returns token)")
        print("3. Use token: Header 'Authorization: Token <token>'")
        print("4. Get user info: GET /api/auth/me/")
        print("5. Update profile: PUT/PATCH /api/auth/profile/")
        print("6. Change password: POST /api/auth/change-password/")
        print("7. Logout: POST /api/auth/logout/")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
