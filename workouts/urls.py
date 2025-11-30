from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .views import ExerciseViewSet, WorkoutViewSet, WorkoutSessionViewSet, ExerciseLogViewSet
from . import auth_views


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint for Docker and K8s."""
    return Response({'status': 'healthy', 'service': 'workout-api'})

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'exercises', ExerciseViewSet, basename='exercise')
router.register(r'workouts', WorkoutViewSet, basename='workout')
router.register(r'sessions', WorkoutSessionViewSet, basename='session')
router.register(r'logs', ExerciseLogViewSet, basename='log')

# The API URLs are determined automatically by the router
urlpatterns = [
    # Health check endpoint
    path('health/', health_check, name='health-check'),

    # Authentication endpoints
    path('auth/register/', auth_views.register, name='auth-register'),
    path('auth/login/', auth_views.login, name='auth-login'),
    path('auth/logout/', auth_views.logout, name='auth-logout'),
    path('auth/me/', auth_views.get_current_user, name='auth-me'),
    path('auth/profile/', auth_views.update_profile, name='auth-update-profile'),
    path('auth/change-password/', auth_views.change_password, name='auth-change-password'),

    # Router URLs
    path('', include(router.urls)),
]
