from rest_framework import serializers
from .models import UserProfile, Exercise, Workout, WorkoutExercise, WorkoutSession, ExerciseLog


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for UserProfile model.
    """
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'user_id', 'username', 'email', 'height', 'weight',
                  'date_of_birth', 'fitness_goal', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user_id', 'username', 'email', 'created_at', 'updated_at']


class ExerciseSerializer(serializers.ModelSerializer):
    """
    Serializer for Exercise model.
    """
    class Meta:
        model = Exercise
        fields = ['id', 'name', 'description', 'category', 'muscle_groups',
                  'equipment_required', 'difficulty', 'video_url', 'image_url',
                  'instructions', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ExerciseListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing exercises.
    """
    class Meta:
        model = Exercise
        fields = ['id', 'name', 'category', 'difficulty', 'muscle_groups']


class WorkoutExerciseSerializer(serializers.ModelSerializer):
    """
    Serializer for WorkoutExercise model.
    """
    exercise = ExerciseListSerializer(read_only=True)
    exercise_id = serializers.PrimaryKeyRelatedField(
        queryset=Exercise.objects.all(),
        source='exercise',
        write_only=True
    )

    class Meta:
        model = WorkoutExercise
        fields = ['id', 'exercise', 'exercise_id', 'order', 'sets', 'reps',
                  'duration', 'rest_period', 'notes']
        read_only_fields = ['id']


class WorkoutSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for Workout model.
    """
    exercises = WorkoutExerciseSerializer(many=True, required=False)
    creator = UserProfileSerializer(read_only=True)
    creator_username = serializers.CharField(source='creator.user.username', read_only=True)
    total_exercises = serializers.SerializerMethodField()

    class Meta:
        model = Workout
        fields = ['id', 'title', 'description', 'creator', 'creator_username',
                  'is_public', 'exercises', 'estimated_duration', 'difficulty',
                  'tags', 'total_exercises', 'created_at', 'updated_at']
        read_only_fields = ['id', 'creator', 'creator_username', 'created_at', 'updated_at']

    def get_total_exercises(self, obj):
        """Get total number of exercises in the workout."""
        return obj.get_total_exercises()

    def create(self, validated_data):
        """Create workout with exercises."""
        exercises_data = validated_data.pop('exercises', [])

        # Get or create UserProfile for the authenticated user
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
            validated_data['creator'] = user_profile

        # Create workout
        workout = Workout.objects.create(**validated_data)

        # Create WorkoutExercise objects
        for exercise_data in exercises_data:
            WorkoutExercise.objects.create(workout=workout, **exercise_data)

        return workout

    def update(self, instance, validated_data):
        """Update workout."""
        exercises_data = validated_data.pop('exercises', None)

        # Update basic fields
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()

        # Update exercises if provided
        if exercises_data is not None:
            # Delete existing exercises and create new ones
            instance.exercises.all().delete()
            for exercise_data in exercises_data:
                WorkoutExercise.objects.create(workout=instance, **exercise_data)

        return instance


class WorkoutListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing workouts.
    """
    creator_username = serializers.CharField(source='creator.user.username', read_only=True)
    total_exercises = serializers.SerializerMethodField()

    class Meta:
        model = Workout
        fields = ['id', 'title', 'creator_username', 'difficulty', 'estimated_duration',
                  'total_exercises', 'is_public', 'tags', 'created_at']

    def get_total_exercises(self, obj):
        return obj.get_total_exercises()


class WorkoutSessionSerializer(serializers.ModelSerializer):
    """
    Serializer for WorkoutSession model.
    """
    user = UserProfileSerializer(read_only=True)
    workout = WorkoutListSerializer(read_only=True)
    workout_id = serializers.PrimaryKeyRelatedField(
        queryset=Workout.objects.all(),
        source='workout',
        write_only=True
    )
    duration_minutes = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()

    class Meta:
        model = WorkoutSession
        fields = ['id', 'user', 'workout', 'workout_id', 'status', 'scheduled_date',
                  'started_at', 'completed_at', 'duration_minutes', 'notes',
                  'created_at', 'updated_at', 'date']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'date']

    def get_duration_minutes(self, obj):
        """Get session duration in minutes."""
        return obj.get_duration()

    def get_date(self, obj):
        """Get the session date - uses completed_at, started_at, or scheduled_date."""
        if obj.completed_at:
            return obj.completed_at.date().isoformat()
        elif obj.started_at:
            return obj.started_at.date().isoformat()
        elif obj.scheduled_date:
            return obj.scheduled_date.date().isoformat()
        return obj.created_at.date().isoformat()

    def create(self, validated_data):
        """Create workout session."""
        # Get or create user profile
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
            validated_data['user'] = user_profile

        return WorkoutSession.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """Update workout session."""
        # Don't allow changing user or workout
        validated_data.pop('user', None)
        validated_data.pop('workout', None)

        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()

        return instance


class WorkoutSessionListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing workout sessions.
    """
    workout_title = serializers.CharField(source='workout.title', read_only=True)
    duration_minutes = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()

    class Meta:
        model = WorkoutSession
        fields = ['id', 'workout_title', 'status', 'scheduled_date', 'started_at',
                  'completed_at', 'duration_minutes', 'created_at', 'date']

    def get_duration_minutes(self, obj):
        return obj.get_duration()

    def get_date(self, obj):
        """Get the session date - uses completed_at, started_at, or scheduled_date."""
        if obj.completed_at:
            return obj.completed_at.date().isoformat()
        elif obj.started_at:
            return obj.started_at.date().isoformat()
        elif obj.scheduled_date:
            return obj.scheduled_date.date().isoformat()
        return obj.created_at.date().isoformat()


class ExerciseLogSerializer(serializers.ModelSerializer):
    """
    Serializer for ExerciseLog model.
    """
    exercise = ExerciseListSerializer(read_only=True)
    exercise_id = serializers.PrimaryKeyRelatedField(
        queryset=Exercise.objects.all(),
        source='exercise',
        write_only=True
    )
    session_id = serializers.PrimaryKeyRelatedField(
        queryset=WorkoutSession.objects.all(),
        source='session',
        write_only=True
    )

    class Meta:
        model = ExerciseLog
        fields = ['id', 'session_id', 'exercise', 'exercise_id', 'set_number',
                  'reps', 'weight', 'duration', 'distance', 'notes',
                  'perceived_exertion', 'created_at']
        read_only_fields = ['id', 'created_at']


class ExerciseLogListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing exercise logs.
    """
    exercise_name = serializers.CharField(source='exercise.name', read_only=True)

    class Meta:
        model = ExerciseLog
        fields = ['id', 'exercise_name', 'set_number', 'reps', 'weight',
                  'duration', 'created_at']
