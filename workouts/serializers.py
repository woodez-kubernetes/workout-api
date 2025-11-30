from rest_framework import serializers
from .models import UserProfile, Exercise, Workout, WorkoutExercise, WorkoutSession, ExerciseLog


class UserProfileSerializer(serializers.Serializer):
    """
    Serializer for UserProfile model.
    """
    id = serializers.CharField(read_only=True)
    user_id = serializers.IntegerField(required=True)
    username = serializers.CharField(max_length=150, required=True)
    email = serializers.EmailField(required=True)
    height = serializers.IntegerField(required=False, allow_null=True)
    weight = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    date_of_birth = serializers.DateTimeField(required=False, allow_null=True)
    fitness_goal = serializers.ChoiceField(choices=UserProfile.FITNESS_GOAL_CHOICES, default='general')
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def create(self, validated_data):
        return UserProfile(**validated_data).save()

    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance


class ExerciseSerializer(serializers.Serializer):
    """
    Serializer for Exercise model.
    """
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(max_length=200, required=True)
    description = serializers.CharField(required=True)
    category = serializers.ChoiceField(choices=Exercise.CATEGORY_CHOICES, required=True)
    muscle_groups = serializers.ListField(child=serializers.CharField(max_length=50), required=False, default=list)
    equipment_required = serializers.ListField(child=serializers.CharField(max_length=50), required=False, default=list)
    difficulty = serializers.ChoiceField(choices=Exercise.DIFFICULTY_CHOICES, required=True)
    video_url = serializers.URLField(required=False, allow_null=True)
    image_url = serializers.URLField(required=False, allow_null=True)
    instructions = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def create(self, validated_data):
        return Exercise(**validated_data).save()

    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance


class ExerciseListSerializer(serializers.Serializer):
    """
    Lightweight serializer for listing exercises.
    """
    id = serializers.CharField(read_only=True)
    name = serializers.CharField()
    category = serializers.CharField()
    difficulty = serializers.CharField()
    muscle_groups = serializers.ListField()


class WorkoutExerciseSerializer(serializers.Serializer):
    """
    Serializer for WorkoutExercise embedded document.
    """
    exercise = ExerciseListSerializer(read_only=True)
    exercise_id = serializers.CharField(write_only=True, required=True)
    order = serializers.IntegerField(required=True, min_value=1)
    sets = serializers.IntegerField(default=3, min_value=1)
    reps = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    duration = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    rest_period = serializers.IntegerField(default=60)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate_exercise_id(self, value):
        """Validate that the exercise exists."""
        try:
            Exercise.objects.get(id=value)
        except Exercise.DoesNotExist:
            raise serializers.ValidationError("Exercise not found.")
        return value

    def to_representation(self, instance):
        """Convert MongoEngine embedded document to dict."""
        return {
            'exercise': ExerciseListSerializer(instance.exercise).data if instance.exercise else None,
            'order': instance.order,
            'sets': instance.sets,
            'reps': instance.reps,
            'duration': instance.duration,
            'rest_period': instance.rest_period,
            'notes': instance.notes,
        }


class WorkoutSerializer(serializers.Serializer):
    """
    Detailed serializer for Workout model.
    """
    id = serializers.CharField(read_only=True)
    title = serializers.CharField(max_length=200, required=True)
    description = serializers.CharField(required=True)
    creator = UserProfileSerializer(read_only=True)
    is_public = serializers.BooleanField(default=False)
    exercises = WorkoutExerciseSerializer(many=True, required=False)
    estimated_duration = serializers.IntegerField(required=False, allow_null=True)
    difficulty = serializers.ChoiceField(choices=Workout.DIFFICULTY_CHOICES, required=True)
    tags = serializers.ListField(child=serializers.CharField(max_length=50), required=False, default=list)
    total_exercises = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def get_total_exercises(self, obj):
        """Get total number of exercises in the workout."""
        return obj.get_total_exercises()

    def create(self, validated_data):
        """Create workout with exercises."""
        exercises_data = validated_data.pop('exercises', [])

        # Get creator from request context
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            # Get or create UserProfile for the authenticated user
            user_profile, _ = UserProfile.objects.get_or_create(
                user_id=request.user.id,
                defaults={
                    'username': request.user.username,
                    'email': request.user.email,
                }
            )
            validated_data['creator'] = user_profile

        # Create workout without exercises first
        workout = Workout(
            title=validated_data['title'],
            description=validated_data['description'],
            creator=validated_data.get('creator'),
            is_public=validated_data.get('is_public', False),
            estimated_duration=validated_data.get('estimated_duration'),
            difficulty=validated_data['difficulty'],
            tags=validated_data.get('tags', []),
        )

        # Add exercises
        for exercise_data in exercises_data:
            exercise_id = exercise_data.pop('exercise_id')
            exercise = Exercise.objects.get(id=exercise_id)
            workout_exercise = WorkoutExercise(exercise=exercise, **exercise_data)
            workout.exercises.append(workout_exercise)

        workout.save()
        return workout

    def update(self, instance, validated_data):
        """Update workout."""
        exercises_data = validated_data.pop('exercises', None)

        # Update basic fields
        for key, value in validated_data.items():
            if key != 'creator':  # Don't update creator
                setattr(instance, key, value)

        # Update exercises if provided
        if exercises_data is not None:
            instance.exercises = []
            for exercise_data in exercises_data:
                exercise_id = exercise_data.pop('exercise_id')
                exercise = Exercise.objects.get(id=exercise_id)
                workout_exercise = WorkoutExercise(exercise=exercise, **exercise_data)
                instance.exercises.append(workout_exercise)

        instance.save()
        return instance

    def to_representation(self, instance):
        """Convert MongoEngine document to dict."""
        return {
            'id': str(instance.id),
            'title': instance.title,
            'description': instance.description,
            'creator': UserProfileSerializer(instance.creator).data if instance.creator else None,
            'is_public': instance.is_public,
            'exercises': [WorkoutExerciseSerializer(ex).to_representation(ex) for ex in instance.exercises],
            'estimated_duration': instance.estimated_duration,
            'difficulty': instance.difficulty,
            'tags': instance.tags,
            'total_exercises': instance.get_total_exercises(),
            'created_at': instance.created_at.isoformat() if instance.created_at else None,
            'updated_at': instance.updated_at.isoformat() if instance.updated_at else None,
        }


class WorkoutListSerializer(serializers.Serializer):
    """
    Lightweight serializer for listing workouts.
    """
    id = serializers.CharField(read_only=True)
    title = serializers.CharField()
    creator_username = serializers.SerializerMethodField()
    difficulty = serializers.CharField()
    estimated_duration = serializers.IntegerField()
    total_exercises = serializers.SerializerMethodField()
    is_public = serializers.BooleanField()
    tags = serializers.ListField()
    created_at = serializers.DateTimeField()

    def get_creator_username(self, obj):
        return obj.creator.username if obj.creator else None

    def get_total_exercises(self, obj):
        return obj.get_total_exercises()


class WorkoutSessionSerializer(serializers.Serializer):
    """
    Serializer for WorkoutSession model.
    """
    id = serializers.CharField(read_only=True)
    user = UserProfileSerializer(read_only=True)
    workout = WorkoutListSerializer(read_only=True)
    workout_id = serializers.CharField(write_only=True, required=True)
    status = serializers.ChoiceField(choices=WorkoutSession.STATUS_CHOICES, default='planned')
    scheduled_date = serializers.DateTimeField(required=False, allow_null=True)
    started_at = serializers.DateTimeField(required=False, allow_null=True)
    completed_at = serializers.DateTimeField(required=False, allow_null=True)
    duration_minutes = serializers.SerializerMethodField()
    notes = serializers.CharField(required=False, allow_blank=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def get_duration_minutes(self, obj):
        """Get session duration in minutes."""
        return obj.get_duration()

    def validate_workout_id(self, value):
        """Validate that the workout exists."""
        try:
            Workout.objects.get(id=value)
        except Workout.DoesNotExist:
            raise serializers.ValidationError("Workout not found.")
        return value

    def create(self, validated_data):
        """Create workout session."""
        workout_id = validated_data.pop('workout_id')
        workout = Workout.objects.get(id=workout_id)

        # Get user from request context
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user_profile, _ = UserProfile.objects.get_or_create(
                user_id=request.user.id,
                defaults={
                    'username': request.user.username,
                    'email': request.user.email,
                }
            )
            validated_data['user'] = user_profile

        validated_data['workout'] = workout
        session = WorkoutSession(**validated_data)
        session.save()
        return session

    def update(self, instance, validated_data):
        """Update workout session."""
        validated_data.pop('workout_id', None)  # Don't allow changing the workout

        for key, value in validated_data.items():
            if key not in ['user', 'workout']:  # Don't update these
                setattr(instance, key, value)

        instance.save()
        return instance

    def to_representation(self, instance):
        """Convert MongoEngine document to dict."""
        return {
            'id': str(instance.id),
            'user': UserProfileSerializer(instance.user).data if instance.user else None,
            'workout': WorkoutListSerializer(instance.workout).data if instance.workout else None,
            'status': instance.status,
            'scheduled_date': instance.scheduled_date.isoformat() if instance.scheduled_date else None,
            'started_at': instance.started_at.isoformat() if instance.started_at else None,
            'completed_at': instance.completed_at.isoformat() if instance.completed_at else None,
            'duration_minutes': instance.get_duration(),
            'notes': instance.notes,
            'created_at': instance.created_at.isoformat() if instance.created_at else None,
            'updated_at': instance.updated_at.isoformat() if instance.updated_at else None,
        }


class WorkoutSessionListSerializer(serializers.Serializer):
    """
    Lightweight serializer for listing workout sessions.
    """
    id = serializers.CharField()
    workout_title = serializers.SerializerMethodField()
    status = serializers.CharField()
    scheduled_date = serializers.DateTimeField()
    started_at = serializers.DateTimeField()
    completed_at = serializers.DateTimeField()
    duration_minutes = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField()

    def get_workout_title(self, obj):
        return obj.workout.title if obj.workout else None

    def get_duration_minutes(self, obj):
        return obj.get_duration()


class ExerciseLogSerializer(serializers.Serializer):
    """
    Serializer for ExerciseLog model.
    """
    id = serializers.CharField(read_only=True)
    session_id = serializers.CharField(write_only=True, required=True)
    exercise = ExerciseListSerializer(read_only=True)
    exercise_id = serializers.CharField(write_only=True, required=True)
    set_number = serializers.IntegerField(required=True, min_value=1)
    reps = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    weight = serializers.DecimalField(max_digits=6, decimal_places=2, required=False, allow_null=True, min_value=0)
    duration = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    distance = serializers.DecimalField(max_digits=6, decimal_places=2, required=False, allow_null=True, min_value=0)
    notes = serializers.CharField(required=False, allow_blank=True)
    perceived_exertion = serializers.IntegerField(required=False, allow_null=True, min_value=1, max_value=10)
    created_at = serializers.DateTimeField(read_only=True)

    def validate_exercise_id(self, value):
        """Validate that the exercise exists."""
        try:
            Exercise.objects.get(id=value)
        except Exercise.DoesNotExist:
            raise serializers.ValidationError("Exercise not found.")
        return value

    def validate_session_id(self, value):
        """Validate that the session exists."""
        try:
            WorkoutSession.objects.get(id=value)
        except WorkoutSession.DoesNotExist:
            raise serializers.ValidationError("Workout session not found.")
        return value

    def create(self, validated_data):
        """Create exercise log."""
        exercise_id = validated_data.pop('exercise_id')
        session_id = validated_data.pop('session_id')

        exercise = Exercise.objects.get(id=exercise_id)
        session = WorkoutSession.objects.get(id=session_id)

        validated_data['exercise'] = exercise
        validated_data['session'] = session

        log = ExerciseLog(**validated_data)
        log.save()
        return log

    def update(self, instance, validated_data):
        """Update exercise log."""
        validated_data.pop('exercise_id', None)  # Don't allow changing exercise
        validated_data.pop('session_id', None)  # Don't allow changing session

        for key, value in validated_data.items():
            if key not in ['exercise', 'session']:
                setattr(instance, key, value)

        instance.save()
        return instance

    def to_representation(self, instance):
        """Convert MongoEngine document to dict."""
        return {
            'id': str(instance.id),
            'exercise': ExerciseListSerializer(instance.exercise).data if instance.exercise else None,
            'set_number': instance.set_number,
            'reps': instance.reps,
            'weight': float(instance.weight) if instance.weight else None,
            'duration': instance.duration,
            'distance': float(instance.distance) if instance.distance else None,
            'notes': instance.notes,
            'perceived_exertion': instance.perceived_exertion,
            'created_at': instance.created_at.isoformat() if instance.created_at else None,
        }


class ExerciseLogListSerializer(serializers.Serializer):
    """
    Lightweight serializer for listing exercise logs.
    """
    id = serializers.CharField()
    exercise_name = serializers.SerializerMethodField()
    set_number = serializers.IntegerField()
    reps = serializers.IntegerField()
    weight = serializers.DecimalField(max_digits=6, decimal_places=2)
    duration = serializers.IntegerField()
    created_at = serializers.DateTimeField()

    def get_exercise_name(self, obj):
        return obj.exercise.name if obj.exercise else None
