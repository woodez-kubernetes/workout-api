#!/usr/bin/env python
"""
Test script to verify API endpoints are configured correctly.
This tests URL routing and view configuration without requiring MongoDB.
"""
import os
import sys
import django

# Setup Django testingbbbb
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.urls import get_resolver
from rest_framework.test import APIRequestFactory, force_authenticate
from django.contrib.auth.models import User
from workouts.views import ExerciseViewSet, WorkoutViewSet, WorkoutSessionViewSet, ExerciseLogViewSet


def test_url_patterns():
    """Test that URL patterns are configured correctly."""
    print("\n" + "="*60)
    print("Testing URL Patterns")
    print("="*60)

    from django.urls import reverse, NoReverseMatch

    # Test that we can reverse key URL patterns
    test_urls = [
        ('exercise-list', 'GET /api/exercises/'),
        ('workout-list', 'GET /api/workouts/'),
        ('session-list', 'GET /api/sessions/'),
        ('log-list', 'GET /api/logs/'),
        ('schema', 'GET /api/schema/'),
        ('swagger-ui', 'GET /api/docs/'),
        ('redoc', 'GET /api/redoc/'),
    ]

    print("\nTesting URL reversing:")
    failed = []
    for url_name, description in test_urls:
        try:
            path = reverse(url_name)
            print(f"  ✓ {description} -> {path}")
        except NoReverseMatch as e:
            print(f"  ❌ {description} -> Failed to reverse")
            failed.append(url_name)

    # Test detail URLs
    print("\nTesting detail URLs:")
    detail_urls = [
        ('exercise-detail', {'pk': 'test-id'}, 'GET /api/exercises/{id}/'),
        ('workout-detail', {'pk': 'test-id'}, 'GET /api/workouts/{id}/'),
        ('session-detail', {'pk': 'test-id'}, 'GET /api/sessions/{id}/'),
        ('log-detail', {'pk': 'test-id'}, 'GET /api/logs/{id}/'),
    ]

    for url_name, kwargs, description in detail_urls:
        try:
            path = reverse(url_name, kwargs=kwargs)
            print(f"  ✓ {description} -> {path}")
        except NoReverseMatch:
            print(f"  ❌ {description} -> Failed to reverse")
            failed.append(url_name)

    # Test custom actions
    print("\nTesting custom action URLs:")
    action_urls = [
        ('workout-clone', {'pk': 'test-id'}, 'POST /api/workouts/{id}/clone/'),
        ('session-start', {'pk': 'test-id'}, 'POST /api/sessions/{id}/start/'),
        ('session-complete', {'pk': 'test-id'}, 'POST /api/sessions/{id}/complete/'),
    ]

    for url_name, kwargs, description in action_urls:
        try:
            path = reverse(url_name, kwargs=kwargs)
            print(f"  ✓ {description} -> {path}")
        except NoReverseMatch:
            print(f"  ❌ {description} -> Failed to reverse")
            failed.append(url_name)

    if failed:
        print(f"\n❌ Failed to reverse {len(failed)} URLs: {failed}")
        return False
    else:
        print(f"\n✅ All URL patterns configured correctly!")
        return True


def test_viewsets():
    """Test that ViewSets are configured correctly."""
    print("\n" + "="*60)
    print("Testing ViewSets")
    print("="*60)

    factory = APIRequestFactory()

    # Test ExerciseViewSet
    print("\n1. ExerciseViewSet")
    try:
        view = ExerciseViewSet.as_view({'get': 'list'})
        request = factory.get('/api/exercises/')
        print("   ✓ ExerciseViewSet.list - configured")

        view = ExerciseViewSet.as_view({'post': 'create'})
        request = factory.post('/api/exercises/')
        print("   ✓ ExerciseViewSet.create - configured")

        view = ExerciseViewSet.as_view({'get': 'retrieve'})
        print("   ✓ ExerciseViewSet.retrieve - configured")
    except Exception as e:
        print(f"   ❌ ExerciseViewSet error: {e}")
        return False

    # Test WorkoutViewSet
    print("\n2. WorkoutViewSet")
    try:
        view = WorkoutViewSet.as_view({'get': 'list'})
        print("   ✓ WorkoutViewSet.list - configured")

        view = WorkoutViewSet.as_view({'post': 'create'})
        print("   ✓ WorkoutViewSet.create - configured")

        view = WorkoutViewSet.as_view({'post': 'clone'})
        print("   ✓ WorkoutViewSet.clone (custom action) - configured")
    except Exception as e:
        print(f"   ❌ WorkoutViewSet error: {e}")
        return False

    # Test WorkoutSessionViewSet
    print("\n3. WorkoutSessionViewSet")
    try:
        view = WorkoutSessionViewSet.as_view({'get': 'list'})
        print("   ✓ WorkoutSessionViewSet.list - configured")

        view = WorkoutSessionViewSet.as_view({'post': 'start'})
        print("   ✓ WorkoutSessionViewSet.start (custom action) - configured")

        view = WorkoutSessionViewSet.as_view({'post': 'complete'})
        print("   ✓ WorkoutSessionViewSet.complete (custom action) - configured")
    except Exception as e:
        print(f"   ❌ WorkoutSessionViewSet error: {e}")
        return False

    # Test ExerciseLogViewSet
    print("\n4. ExerciseLogViewSet")
    try:
        view = ExerciseLogViewSet.as_view({'get': 'list'})
        print("   ✓ ExerciseLogViewSet.list - configured")

        view = ExerciseLogViewSet.as_view({'post': 'create'})
        print("   ✓ ExerciseLogViewSet.create - configured")
    except Exception as e:
        print(f"   ❌ ExerciseLogViewSet error: {e}")
        return False

    print("\n✅ All ViewSets configured correctly!")
    return True


def test_permissions():
    """Test that permission classes are imported correctly."""
    print("\n" + "="*60)
    print("Testing Permission Classes")
    print("="*60)

    try:
        from workouts.permissions import IsOwnerOrReadOnly, IsAdminOrReadOnly
        print("\n✓ IsOwnerOrReadOnly - imported successfully")
        print("✓ IsAdminOrReadOnly - imported successfully")

        # Check that ViewSets use permissions
        print("\nViewSet Permissions:")
        print(f"  ExerciseViewSet: {ExerciseViewSet.permission_classes}")
        print(f"  WorkoutViewSet: {WorkoutViewSet.permission_classes}")
        print(f"  WorkoutSessionViewSet: {WorkoutSessionViewSet.permission_classes}")
        print(f"  ExerciseLogViewSet: {ExerciseLogViewSet.permission_classes}")

        print("\n✅ Permission classes configured!")
        return True
    except Exception as e:
        print(f"❌ Permission error: {e}")
        return False


def test_serializers():
    """Test that serializers are imported correctly."""
    print("\n" + "="*60)
    print("Testing Serializers")
    print("="*60)

    try:
        from workouts.serializers import (
            ExerciseSerializer,
            ExerciseListSerializer,
            WorkoutSerializer,
            WorkoutListSerializer,
            WorkoutSessionSerializer,
            WorkoutSessionListSerializer,
            ExerciseLogSerializer,
            ExerciseLogListSerializer,
        )

        serializers = [
            'ExerciseSerializer',
            'ExerciseListSerializer',
            'WorkoutSerializer',
            'WorkoutListSerializer',
            'WorkoutSessionSerializer',
            'WorkoutSessionListSerializer',
            'ExerciseLogSerializer',
            'ExerciseLogListSerializer',
        ]

        print(f"\n✓ Found {len(serializers)} serializers:")
        for s in serializers:
            print(f"  - {s}")

        print("\n✅ All serializers imported successfully!")
        return True
    except Exception as e:
        print(f"❌ Serializer error: {e}")
        return False


def test_models():
    """Test that models are imported correctly."""
    print("\n" + "="*60)
    print("Testing Models")
    print("="*60)

    try:
        from workouts.models import (
            UserProfile,
            Exercise,
            Workout,
            WorkoutExercise,
            WorkoutSession,
            ExerciseLog,
        )

        models = [
            'UserProfile',
            'Exercise',
            'Workout',
            'WorkoutExercise (EmbeddedDocument)',
            'WorkoutSession',
            'ExerciseLog',
        ]

        print(f"\n✓ Found {len(models)} models:")
        for m in models:
            print(f"  - {m}")

        # Test model choices
        print("\nModel Choices:")
        print(f"  Exercise categories: {len(Exercise.CATEGORY_CHOICES)}")
        print(f"  Exercise difficulties: {len(Exercise.DIFFICULTY_CHOICES)}")
        print(f"  Workout difficulties: {len(Workout.DIFFICULTY_CHOICES)}")
        print(f"  Session statuses: {len(WorkoutSession.STATUS_CHOICES)}")
        print(f"  Fitness goals: {len(UserProfile.FITNESS_GOAL_CHOICES)}")

        print("\n✅ All models imported successfully!")
        return True
    except Exception as e:
        print(f"❌ Model error: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("WORKOUT API - ENDPOINT TESTING")
    print("="*60)
    print("\nTesting API configuration without requiring MongoDB connection...")

    results = []

    # Run tests
    results.append(("URL Patterns", test_url_patterns()))
    results.append(("Models", test_models()))
    results.append(("Serializers", test_serializers()))
    results.append(("ViewSets", test_viewsets()))
    results.append(("Permissions", test_permissions()))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All API endpoints are configured correctly!")
        print("\nNext steps:")
        print("1. Ensure MongoDB is running (locally or in K8s)")
        print("2. Run 'python manage.py runserver' to start the API")
        print("3. Visit http://localhost:8000/api/docs/ for Swagger UI")
        print("4. Create a superuser: python manage.py createsuperuser")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
