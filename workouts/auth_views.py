from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import UserProfile
from .serializers import UserProfileSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Register a new user.

    Request body:
    {
        "username": "string",
        "email": "string",
        "password": "string",
        "password_confirm": "string",
        "first_name": "string" (optional),
        "last_name": "string" (optional),
        "height": integer (optional),
        "weight": decimal (optional),
        "fitness_goal": "string" (optional)
    }
    """
    # Get data
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    password_confirm = request.data.get('password_confirm')
    first_name = request.data.get('first_name', '')
    last_name = request.data.get('last_name', '')

    # Validate required fields
    if not username or not email or not password:
        return Response(
            {'error': 'Username, email, and password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Validate password confirmation
    if password != password_confirm:
        return Response(
            {'error': 'Passwords do not match'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Validate password strength
    try:
        validate_password(password)
    except ValidationError as e:
        return Response(
            {'error': list(e.messages)},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check if username already exists
    if User.objects.filter(username=username).exists():
        return Response(
            {'error': 'Username already exists'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check if email already exists
    if User.objects.filter(email=email).exists():
        return Response(
            {'error': 'Email already exists'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Create user
    try:
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # Create UserProfile
        profile_data = {
            'user_id': user.id,
            'username': username,
            'email': email,
        }

        # Add optional profile fields
        if request.data.get('height'):
            profile_data['height'] = request.data.get('height')
        if request.data.get('weight'):
            profile_data['weight'] = request.data.get('weight')
        if request.data.get('fitness_goal'):
            profile_data['fitness_goal'] = request.data.get('fitness_goal')

        # Try to create UserProfile in MongoDB (optional during development)
        user_profile = None
        profile_created = False
        try:
            user_profile = UserProfile(**profile_data)
            user_profile.save()
            profile_created = True
        except Exception as mongo_error:
            # Log the error but don't fail registration
            print(f"Warning: Failed to create UserProfile in MongoDB: {mongo_error}")
            # User can still authenticate with Django, profile creation can be retried later

        # Create authentication token
        token = Token.objects.create(user=user)

        response_data = {
            'message': 'User registered successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
            'token': token.key
        }

        if profile_created and user_profile:
            response_data['profile'] = UserProfileSerializer(user_profile).data
        else:
            response_data['warning'] = 'User created but profile storage unavailable (MongoDB)'

        return Response(response_data, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response(
            {'error': f'Failed to create user: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Login user and return authentication token.

    Request body:
    {
        "username": "string",
        "password": "string"
    }
    """
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response(
            {'error': 'Username and password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Authenticate user
    user = authenticate(username=username, password=password)

    if user is None:
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Get or create token
    token, created = Token.objects.get_or_create(user=user)

    # Get user profile (optional if MongoDB unavailable)
    profile_data = None
    try:
        user_profile = UserProfile.objects.get(user_id=user.id)
        profile_data = UserProfileSerializer(user_profile).data
    except UserProfile.DoesNotExist:
        # Try to create profile if it doesn't exist
        try:
            user_profile = UserProfile(
                user_id=user.id,
                username=user.username,
                email=user.email
            )
            user_profile.save()
            profile_data = UserProfileSerializer(user_profile).data
        except Exception as mongo_error:
            print(f"Warning: Failed to create UserProfile in MongoDB: {mongo_error}")
            profile_data = None
    except Exception as mongo_error:
        print(f"Warning: Failed to access UserProfile in MongoDB: {mongo_error}")
        profile_data = None

    response_data = {
        'message': 'Login successful',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        },
        'token': token.key
    }

    if profile_data:
        response_data['profile'] = profile_data
    else:
        response_data['warning'] = 'Profile data unavailable (MongoDB connection issue)'

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Logout user by deleting their authentication token.
    """
    try:
        # Delete the user's token
        request.user.auth_token.delete()
        return Response(
            {'message': 'Logout successful'},
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {'error': f'Logout failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    """
    Get current authenticated user's information.
    """
    user = request.user

    # Get user profile (optional if MongoDB unavailable)
    profile_data = None
    try:
        user_profile = UserProfile.objects.get(user_id=user.id)
        profile_data = UserProfileSerializer(user_profile).data
    except UserProfile.DoesNotExist:
        # Try to create profile if it doesn't exist
        try:
            user_profile = UserProfile(
                user_id=user.id,
                username=user.username,
                email=user.email
            )
            user_profile.save()
            profile_data = UserProfileSerializer(user_profile).data
        except Exception as mongo_error:
            print(f"Warning: Failed to create/access UserProfile in MongoDB: {mongo_error}")
            profile_data = None
    except Exception as mongo_error:
        print(f"Warning: Failed to access UserProfile in MongoDB: {mongo_error}")
        profile_data = None

    response_data = {
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
        }
    }

    if profile_data:
        response_data['profile'] = profile_data
    else:
        response_data['warning'] = 'Profile data unavailable (MongoDB connection issue)'

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """
    Update current user's profile.

    Request body (all fields optional):
    {
        "first_name": "string",
        "last_name": "string",
        "email": "string",
        "height": integer,
        "weight": decimal,
        "date_of_birth": "YYYY-MM-DD",
        "fitness_goal": "string"
    }
    """
    user = request.user

    # Update Django User fields
    if 'first_name' in request.data:
        user.first_name = request.data['first_name']
    if 'last_name' in request.data:
        user.last_name = request.data['last_name']
    if 'email' in request.data:
        # Check if email is already taken by another user
        if User.objects.filter(email=request.data['email']).exclude(id=user.id).exists():
            return Response(
                {'error': 'Email already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.email = request.data['email']

    user.save()

    # Update UserProfile (optional if MongoDB unavailable)
    profile_data = None
    profile_updated = False
    try:
        try:
            user_profile = UserProfile.objects.get(user_id=user.id)
        except UserProfile.DoesNotExist:
            # Create profile if it doesn't exist
            user_profile = UserProfile(
                user_id=user.id,
                username=user.username,
                email=user.email
            )

        # Update profile fields
        if 'height' in request.data:
            user_profile.height = request.data['height']
        if 'weight' in request.data:
            user_profile.weight = request.data['weight']
        if 'date_of_birth' in request.data:
            user_profile.date_of_birth = request.data['date_of_birth']
        if 'fitness_goal' in request.data:
            user_profile.fitness_goal = request.data['fitness_goal']

        # Update email in profile to match user
        user_profile.email = user.email

        user_profile.save()
        profile_data = UserProfileSerializer(user_profile).data
        profile_updated = True
    except Exception as mongo_error:
        print(f"Warning: Failed to update UserProfile in MongoDB: {mongo_error}")
        # User model was still updated successfully

    response_data = {
        'message': 'Profile updated successfully',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }
    }

    if profile_updated and profile_data:
        response_data['profile'] = profile_data
    else:
        response_data['warning'] = 'User updated but profile storage unavailable (MongoDB)'

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Change current user's password.

    Request body:
    {
        "old_password": "string",
        "new_password": "string",
        "new_password_confirm": "string"
    }
    """
    user = request.user

    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')
    new_password_confirm = request.data.get('new_password_confirm')

    # Validate required fields
    if not old_password or not new_password or not new_password_confirm:
        return Response(
            {'error': 'All password fields are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check if old password is correct
    if not user.check_password(old_password):
        return Response(
            {'error': 'Old password is incorrect'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Validate new password confirmation
    if new_password != new_password_confirm:
        return Response(
            {'error': 'New passwords do not match'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Validate password strength
    try:
        validate_password(new_password, user=user)
    except ValidationError as e:
        return Response(
            {'error': list(e.messages)},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Set new password
    user.set_password(new_password)
    user.save()

    # Delete old token and create new one
    Token.objects.filter(user=user).delete()
    token = Token.objects.create(user=user)

    return Response({
        'message': 'Password changed successfully',
        'token': token.key  # Return new token
    }, status=status.HTTP_200_OK)
