from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from django.db.models import Q

from .models import Exercise, Workout, WorkoutSession, ExerciseLog, UserProfile
from .serializers import (
    ExerciseSerializer,
    ExerciseListSerializer,
    WorkoutSerializer,
    WorkoutListSerializer,
    WorkoutSessionSerializer,
    WorkoutSessionListSerializer,
    ExerciseLogSerializer,
    ExerciseLogListSerializer,
    UserProfileSerializer,
)
from .permissions import IsOwnerOrReadOnly, IsAdminOrReadOnly


class ExerciseViewSet(viewsets.ViewSet):
    """
    ViewSet for Exercise model.
    Supports listing, retrieving, creating, updating, and deleting exercises.
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        """Get filtered queryset based on query parameters."""
        queryset = Exercise.objects.all()

        # Filter by category
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)

        # Filter by difficulty
        difficulty = self.request.query_params.get('difficulty', None)
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)

        # Filter by muscle group
        muscle_group = self.request.query_params.get('muscle_group', None)
        if muscle_group:
            queryset = queryset.filter(muscle_groups__in=[muscle_group])

        # Search by name
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(name__icontains=search)

        # Order by
        ordering = self.request.query_params.get('ordering', '-created_at')
        if ordering:
            queryset = queryset.order_by(ordering)

        return queryset

    def list(self, request):
        """List all exercises with filtering and pagination."""
        queryset = self.get_queryset()

        # Simple pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size

        exercises = list(queryset[start:end])
        serializer = ExerciseListSerializer(exercises, many=True)

        return Response({
            'count': queryset.count(),
            'results': serializer.data
        })

    def retrieve(self, request, pk=None):
        """Retrieve a single exercise by ID."""
        try:
            exercise = Exercise.objects.get(id=pk)
            serializer = ExerciseSerializer(exercise)
            return Response(serializer.data)
        except Exercise.DoesNotExist:
            return Response(
                {'error': 'Exercise not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    def create(self, request):
        """Create a new exercise (admin only)."""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only administrators can create exercises'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ExerciseSerializer(data=request.data)
        if serializer.is_valid():
            exercise = serializer.save()
            return Response(
                ExerciseSerializer(exercise).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        """Update an exercise (admin only)."""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only administrators can update exercises'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            exercise = Exercise.objects.get(id=pk)
            serializer = ExerciseSerializer(exercise, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exercise.DoesNotExist:
            return Response(
                {'error': 'Exercise not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    def partial_update(self, request, pk=None):
        """Partially update an exercise (admin only)."""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only administrators can update exercises'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            exercise = Exercise.objects.get(id=pk)
            serializer = ExerciseSerializer(exercise, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exercise.DoesNotExist:
            return Response(
                {'error': 'Exercise not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    def destroy(self, request, pk=None):
        """Delete an exercise (admin only)."""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only administrators can delete exercises'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            exercise = Exercise.objects.get(id=pk)
            exercise.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exercise.DoesNotExist:
            return Response(
                {'error': 'Exercise not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class WorkoutViewSet(viewsets.ViewSet):
    """
    ViewSet for Workout model.
    Supports CRUD operations and custom actions like clone.
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        """Get workouts - public ones and user's own workouts."""
        queryset = Workout.objects.all()

        if self.request.user.is_authenticated:
            # Get user profile
            try:
                user_profile = UserProfile.objects.get(user_id=self.request.user.id)
                # Show public workouts + user's own workouts
                queryset = Workout.objects.filter(
                    Q(is_public=True) | Q(creator=user_profile)
                )
            except UserProfile.DoesNotExist:
                # Only show public workouts
                queryset = Workout.objects.filter(is_public=True)
        else:
            # Anonymous users only see public workouts
            queryset = Workout.objects.filter(is_public=True)

        # Filter by difficulty
        difficulty = self.request.query_params.get('difficulty', None)
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)

        # Filter by tags
        tags = self.request.query_params.get('tags', None)
        if tags:
            tag_list = tags.split(',')
            queryset = queryset.filter(tags__in=tag_list)

        # Search by title
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(title__icontains=search)

        # Order by
        ordering = self.request.query_params.get('ordering', '-created_at')
        queryset = queryset.order_by(ordering)

        return queryset

    def list(self, request):
        """List workouts with filtering and pagination."""
        queryset = self.get_queryset()

        # Simple pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size

        workouts = list(queryset[start:end])
        serializer = WorkoutListSerializer(workouts, many=True)

        return Response({
            'count': queryset.count(),
            'results': serializer.data
        })

    def retrieve(self, request, pk=None):
        """Retrieve a single workout by ID."""
        try:
            workout = Workout.objects.get(id=pk)

            # Check permissions - can view if public or owner
            if not workout.is_public:
                if not request.user.is_authenticated:
                    return Response(
                        {'error': 'Authentication required'},
                        status=status.HTTP_401_UNAUTHORIZED
                    )

                user_profile = UserProfile.objects.get(user_id=request.user.id)
                if workout.creator != user_profile:
                    return Response(
                        {'error': 'You do not have permission to view this workout'},
                        status=status.HTTP_403_FORBIDDEN
                    )

            serializer = WorkoutSerializer(workout)
            return Response(serializer.data)
        except Workout.DoesNotExist:
            return Response(
                {'error': 'Workout not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    def create(self, request):
        """Create a new workout."""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        serializer = WorkoutSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            workout = serializer.save()
            return Response(
                WorkoutSerializer(workout).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        """Update a workout (owner only)."""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            workout = Workout.objects.get(id=pk)
            user_profile = UserProfile.objects.get(user_id=request.user.id)

            # Check if user is the creator
            if workout.creator != user_profile:
                return Response(
                    {'error': 'You do not have permission to update this workout'},
                    status=status.HTTP_403_FORBIDDEN
                )

            serializer = WorkoutSerializer(workout, data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Workout.DoesNotExist:
            return Response(
                {'error': 'Workout not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    def partial_update(self, request, pk=None):
        """Partially update a workout (owner only)."""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            workout = Workout.objects.get(id=pk)
            user_profile = UserProfile.objects.get(user_id=request.user.id)

            if workout.creator != user_profile:
                return Response(
                    {'error': 'You do not have permission to update this workout'},
                    status=status.HTTP_403_FORBIDDEN
                )

            serializer = WorkoutSerializer(
                workout,
                data=request.data,
                partial=True,
                context={'request': request}
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Workout.DoesNotExist:
            return Response(
                {'error': 'Workout not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    def destroy(self, request, pk=None):
        """Delete a workout (owner only)."""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            workout = Workout.objects.get(id=pk)
            user_profile = UserProfile.objects.get(user_id=request.user.id)

            if workout.creator != user_profile:
                return Response(
                    {'error': 'You do not have permission to delete this workout'},
                    status=status.HTTP_403_FORBIDDEN
                )

            workout.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Workout.DoesNotExist:
            return Response(
                {'error': 'Workout not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def clone(self, request, pk=None):
        """Clone a workout to the user's library."""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            original_workout = Workout.objects.get(id=pk)

            # Check if workout is accessible (public or owned by user)
            if not original_workout.is_public:
                user_profile = UserProfile.objects.get(user_id=request.user.id)
                if original_workout.creator != user_profile:
                    return Response(
                        {'error': 'You cannot clone a private workout you do not own'},
                        status=status.HTTP_403_FORBIDDEN
                    )

            # Get or create user profile
            user_profile, _ = UserProfile.objects.get_or_create(
                user_id=request.user.id,
                defaults={
                    'username': request.user.username,
                    'email': request.user.email,
                }
            )

            # Clone the workout
            cloned_workout = Workout(
                title=f"{original_workout.title} (Copy)",
                description=original_workout.description,
                creator=user_profile,
                is_public=False,  # Cloned workouts are private by default
                estimated_duration=original_workout.estimated_duration,
                difficulty=original_workout.difficulty,
                tags=original_workout.tags,
            )

            # Clone exercises
            for exercise in original_workout.exercises:
                cloned_workout.exercises.append(exercise)

            cloned_workout.save()

            return Response(
                WorkoutSerializer(cloned_workout).data,
                status=status.HTTP_201_CREATED
            )
        except Workout.DoesNotExist:
            return Response(
                {'error': 'Workout not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class WorkoutSessionViewSet(viewsets.ViewSet):
    """
    ViewSet for WorkoutSession model.
    Supports CRUD operations and custom actions like start and complete.
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get workout sessions for the authenticated user."""
        if not self.request.user.is_authenticated:
            return WorkoutSession.objects.none()

        try:
            user_profile = UserProfile.objects.get(user_id=self.request.user.id)
            queryset = WorkoutSession.objects.filter(user=user_profile)

            # Filter by status
            status_filter = self.request.query_params.get('status', None)
            if status_filter:
                queryset = queryset.filter(status=status_filter)

            # Filter by date range
            date_from = self.request.query_params.get('date_from', None)
            if date_from:
                queryset = queryset.filter(created_at__gte=date_from)

            date_to = self.request.query_params.get('date_to', None)
            if date_to:
                queryset = queryset.filter(created_at__lte=date_to)

            # Order by
            ordering = self.request.query_params.get('ordering', '-created_at')
            queryset = queryset.order_by(ordering)

            return queryset
        except UserProfile.DoesNotExist:
            return WorkoutSession.objects.none()

    def list(self, request):
        """List workout sessions for the authenticated user."""
        queryset = self.get_queryset()

        # Simple pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size

        sessions = list(queryset[start:end])
        serializer = WorkoutSessionListSerializer(sessions, many=True)

        return Response({
            'count': queryset.count(),
            'results': serializer.data
        })

    def retrieve(self, request, pk=None):
        """Retrieve a single workout session."""
        try:
            session = WorkoutSession.objects.get(id=pk)
            user_profile = UserProfile.objects.get(user_id=request.user.id)

            # Check if session belongs to user
            if session.user != user_profile:
                return Response(
                    {'error': 'You do not have permission to view this session'},
                    status=status.HTTP_403_FORBIDDEN
                )

            serializer = WorkoutSessionSerializer(session)
            return Response(serializer.data)
        except WorkoutSession.DoesNotExist:
            return Response(
                {'error': 'Workout session not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    def create(self, request):
        """Create a new workout session."""
        serializer = WorkoutSessionSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            session = serializer.save()
            return Response(
                WorkoutSessionSerializer(session).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        """Update a workout session."""
        try:
            session = WorkoutSession.objects.get(id=pk)
            user_profile = UserProfile.objects.get(user_id=request.user.id)

            if session.user != user_profile:
                return Response(
                    {'error': 'You do not have permission to update this session'},
                    status=status.HTTP_403_FORBIDDEN
                )

            serializer = WorkoutSessionSerializer(
                session,
                data=request.data,
                context={'request': request}
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except WorkoutSession.DoesNotExist:
            return Response(
                {'error': 'Workout session not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    def partial_update(self, request, pk=None):
        """Partially update a workout session."""
        try:
            session = WorkoutSession.objects.get(id=pk)
            user_profile = UserProfile.objects.get(user_id=request.user.id)

            if session.user != user_profile:
                return Response(
                    {'error': 'You do not have permission to update this session'},
                    status=status.HTTP_403_FORBIDDEN
                )

            serializer = WorkoutSessionSerializer(
                session,
                data=request.data,
                partial=True,
                context={'request': request}
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except WorkoutSession.DoesNotExist:
            return Response(
                {'error': 'Workout session not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    def destroy(self, request, pk=None):
        """Delete a workout session."""
        try:
            session = WorkoutSession.objects.get(id=pk)
            user_profile = UserProfile.objects.get(user_id=request.user.id)

            if session.user != user_profile:
                return Response(
                    {'error': 'You do not have permission to delete this session'},
                    status=status.HTTP_403_FORBIDDEN
                )

            session.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except WorkoutSession.DoesNotExist:
            return Response(
                {'error': 'Workout session not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Mark a workout session as started."""
        try:
            session = WorkoutSession.objects.get(id=pk)
            user_profile = UserProfile.objects.get(user_id=request.user.id)

            if session.user != user_profile:
                return Response(
                    {'error': 'You do not have permission to start this session'},
                    status=status.HTTP_403_FORBIDDEN
                )

            session.start_session()
            return Response(WorkoutSessionSerializer(session).data)
        except WorkoutSession.DoesNotExist:
            return Response(
                {'error': 'Workout session not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark a workout session as completed."""
        try:
            session = WorkoutSession.objects.get(id=pk)
            user_profile = UserProfile.objects.get(user_id=request.user.id)

            if session.user != user_profile:
                return Response(
                    {'error': 'You do not have permission to complete this session'},
                    status=status.HTTP_403_FORBIDDEN
                )

            session.complete_session()
            return Response(WorkoutSessionSerializer(session).data)
        except WorkoutSession.DoesNotExist:
            return Response(
                {'error': 'Workout session not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class ExerciseLogViewSet(viewsets.ViewSet):
    """
    ViewSet for ExerciseLog model.
    Allows users to log their exercise performance during workout sessions.
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get exercise logs for the authenticated user's sessions."""
        if not self.request.user.is_authenticated:
            return ExerciseLog.objects.none()

        try:
            user_profile = UserProfile.objects.get(user_id=self.request.user.id)
            user_sessions = WorkoutSession.objects.filter(user=user_profile)
            queryset = ExerciseLog.objects.filter(session__in=user_sessions)

            # Filter by session
            session_id = self.request.query_params.get('session_id', None)
            if session_id:
                queryset = queryset.filter(session=session_id)

            # Filter by exercise
            exercise_id = self.request.query_params.get('exercise_id', None)
            if exercise_id:
                queryset = queryset.filter(exercise=exercise_id)

            # Order by
            ordering = self.request.query_params.get('ordering', '-created_at')
            queryset = queryset.order_by(ordering)

            return queryset
        except UserProfile.DoesNotExist:
            return ExerciseLog.objects.none()

    def list(self, request):
        """List exercise logs for the authenticated user."""
        queryset = self.get_queryset()

        # Simple pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 50))
        start = (page - 1) * page_size
        end = start + page_size

        logs = list(queryset[start:end])
        serializer = ExerciseLogListSerializer(logs, many=True)

        return Response({
            'count': queryset.count(),
            'results': serializer.data
        })

    def retrieve(self, request, pk=None):
        """Retrieve a single exercise log."""
        try:
            log = ExerciseLog.objects.get(id=pk)
            user_profile = UserProfile.objects.get(user_id=request.user.id)

            # Check if log belongs to user's session
            if log.session.user != user_profile:
                return Response(
                    {'error': 'You do not have permission to view this log'},
                    status=status.HTTP_403_FORBIDDEN
                )

            serializer = ExerciseLogSerializer(log)
            return Response(serializer.data)
        except ExerciseLog.DoesNotExist:
            return Response(
                {'error': 'Exercise log not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    def create(self, request):
        """Create a new exercise log."""
        serializer = ExerciseLogSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # Verify the session belongs to the user
            session_id = request.data.get('session_id')
            try:
                session = WorkoutSession.objects.get(id=session_id)
                user_profile = UserProfile.objects.get(user_id=request.user.id)

                if session.user != user_profile:
                    return Response(
                        {'error': 'You can only add logs to your own sessions'},
                        status=status.HTTP_403_FORBIDDEN
                    )

                log = serializer.save()
                return Response(
                    ExerciseLogSerializer(log).data,
                    status=status.HTTP_201_CREATED
                )
            except WorkoutSession.DoesNotExist:
                return Response(
                    {'error': 'Workout session not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            except UserProfile.DoesNotExist:
                return Response(
                    {'error': 'User profile not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        """Update an exercise log."""
        try:
            log = ExerciseLog.objects.get(id=pk)
            user_profile = UserProfile.objects.get(user_id=request.user.id)

            if log.session.user != user_profile:
                return Response(
                    {'error': 'You do not have permission to update this log'},
                    status=status.HTTP_403_FORBIDDEN
                )

            serializer = ExerciseLogSerializer(log, data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ExerciseLog.DoesNotExist:
            return Response(
                {'error': 'Exercise log not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    def partial_update(self, request, pk=None):
        """Partially update an exercise log."""
        try:
            log = ExerciseLog.objects.get(id=pk)
            user_profile = UserProfile.objects.get(user_id=request.user.id)

            if log.session.user != user_profile:
                return Response(
                    {'error': 'You do not have permission to update this log'},
                    status=status.HTTP_403_FORBIDDEN
                )

            serializer = ExerciseLogSerializer(
                log,
                data=request.data,
                partial=True,
                context={'request': request}
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ExerciseLog.DoesNotExist:
            return Response(
                {'error': 'Exercise log not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    def destroy(self, request, pk=None):
        """Delete an exercise log."""
        try:
            log = ExerciseLog.objects.get(id=pk)
            user_profile = UserProfile.objects.get(user_id=request.user.id)

            if log.session.user != user_profile:
                return Response(
                    {'error': 'You do not have permission to delete this log'},
                    status=status.HTTP_403_FORBIDDEN
                )

            log.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ExerciseLog.DoesNotExist:
            return Response(
                {'error': 'Exercise log not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
