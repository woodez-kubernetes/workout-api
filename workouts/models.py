from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField


class UserProfile(models.Model):
    """
    Extended user profile for fitness tracking.
    Linked to Django's User model via OneToOneField.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='workout_profile')

    # Profile information
    height = models.IntegerField(null=True, blank=True, help_text='Height in centimeters')
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text='Weight in kilograms')
    date_of_birth = models.DateField(null=True, blank=True)

    # Fitness preferences
    FITNESS_GOAL_CHOICES = [
        ('strength', 'Strength Training'),
        ('cardio', 'Cardiovascular Health'),
        ('weight_loss', 'Weight Loss'),
        ('weight_gain', 'Weight Gain'),
        ('endurance', 'Endurance'),
        ('flexibility', 'Flexibility'),
        ('general', 'General Fitness'),
    ]
    fitness_goal = models.CharField(max_length=50, choices=FITNESS_GOAL_CHOICES, default='general')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"Profile: {self.user.username}"


class Exercise(models.Model):
    """
    Exercise library - contains all available exercises.
    """
    CATEGORY_CHOICES = [
        ('strength', 'Strength'),
        ('cardio', 'Cardio'),
        ('flexibility', 'Flexibility'),
        ('balance', 'Balance'),
        ('plyometric', 'Plyometric'),
        ('olympic', 'Olympic Lifting'),
        ('powerlifting', 'Powerlifting'),
    ]

    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]

    name = models.CharField(max_length=200, unique=True)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)

    # Metadata
    muscle_groups = ArrayField(models.CharField(max_length=50), default=list, blank=True)
    equipment_required = ArrayField(models.CharField(max_length=100), default=list, blank=True)
    difficulty = models.CharField(max_length=50, choices=DIFFICULTY_CHOICES)

    # Media
    video_url = models.URLField(blank=True)
    image_url = models.URLField(blank=True)

    # Instructions
    instructions = ArrayField(models.TextField(), default=list, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category']),
            models.Index(fields=['difficulty']),
            models.Index(fields=['category', 'difficulty']),
        ]

    def __str__(self):
        return f"{self.name} ({self.category})"


class Workout(models.Model):
    """
    Workout template/plan containing multiple exercises.
    Can be created by users and shared publicly.
    """
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()

    # Creator - reference to UserProfile
    creator = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='workouts')

    # Visibility
    is_public = models.BooleanField(default=False)

    # Workout metadata
    estimated_duration = models.IntegerField(null=True, blank=True, help_text='Estimated duration in minutes')
    difficulty = models.CharField(max_length=50, choices=DIFFICULTY_CHOICES)

    # Tags for categorization
    tags = ArrayField(models.CharField(max_length=50), default=list, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['creator']),
            models.Index(fields=['is_public']),
            models.Index(fields=['difficulty']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.title} by {self.creator.user.username}"

    def get_total_exercises(self):
        """Return the total number of exercises in this workout."""
        return self.exercises.count()

    def calculate_estimated_duration(self):
        """Calculate estimated duration based on exercises."""
        workout_exercises = self.exercises.all()
        if not workout_exercises:
            return 0

        total_seconds = 0
        for workout_exercise in workout_exercises:
            # Estimate time per exercise
            sets = workout_exercise.sets
            rest = workout_exercise.rest_period

            if workout_exercise.duration:
                exercise_time = workout_exercise.duration * sets
            else:
                # Assume 30 seconds per set if reps-based
                exercise_time = 30 * sets

            # Add rest periods (n-1 rest periods for n sets)
            total_time = exercise_time + (rest * (sets - 1))
            total_seconds += total_time

        # Add 5 minutes for warm-up/cool-down
        total_seconds += 300

        return total_seconds // 60  # Convert to minutes


class WorkoutExercise(models.Model):
    """
    Represents an exercise within a workout.
    Previously an EmbeddedDocument, now a separate table with ForeignKey.
    """
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE, related_name='exercises')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    order = models.IntegerField()

    # Sets and reps
    sets = models.IntegerField(default=3)
    reps = models.IntegerField(null=True, blank=True)  # Optional - for counted exercises
    duration = models.IntegerField(null=True, blank=True)  # Optional - for timed exercises (seconds)

    # Rest period between sets
    rest_period = models.IntegerField(default=60, help_text='Rest period in seconds')

    # Additional notes
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['order']
        unique_together = [['workout', 'order']]

    def __str__(self):
        return f"{self.exercise.name} - {self.sets}x{self.reps or 'timed'}"


class WorkoutSession(models.Model):
    """
    An actual instance of a workout being performed or planned.
    Tracks when a user does a specific workout.
    """
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('skipped', 'Skipped'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='sessions')
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE, related_name='sessions')

    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='planned')

    # Scheduling
    scheduled_date = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # User notes
    notes = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['workout']),
            models.Index(fields=['status']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', '-completed_at']),
        ]

    def __str__(self):
        return f"{self.user.user.username} - {self.workout.title} ({self.status})"

    def start_session(self):
        """Mark session as started."""
        from django.utils import timezone
        self.status = 'in_progress'
        self.started_at = timezone.now()
        self.save()

    def complete_session(self):
        """Mark session as completed."""
        from django.utils import timezone
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()

    def get_duration(self):
        """Get actual duration of the session in minutes."""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds() / 60
        return None


class ExerciseLog(models.Model):
    """
    Log of individual exercise performance within a workout session.
    Tracks actual sets, reps, weight, etc.
    """
    session = models.ForeignKey(WorkoutSession, on_delete=models.CASCADE, related_name='logs')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)

    # Set information
    set_number = models.IntegerField()

    # Performance data
    reps = models.IntegerField(null=True, blank=True)  # Actual reps completed
    weight = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)  # Weight in kg
    duration = models.IntegerField(null=True, blank=True)  # Duration in seconds (for timed exercises)
    distance = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)  # Distance in km (for cardio)

    # Notes for this specific set
    notes = models.TextField(blank=True)

    # Perceived difficulty (1-10 scale)
    perceived_exertion = models.IntegerField(null=True, blank=True)

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['session']),
            models.Index(fields=['exercise']),
            models.Index(fields=['created_at']),
            models.Index(fields=['session', 'exercise']),
            models.Index(fields=['exercise', '-created_at']),
        ]

    def __str__(self):
        return f"{self.exercise.name} - Set {self.set_number}: {self.reps}x{self.weight}kg"
