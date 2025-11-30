from mongoengine import Document, EmbeddedDocument, fields
from django.contrib.auth.models import User
from datetime import datetime


class UserProfile(Document):
    """
    Extended user profile for fitness tracking.
    Linked to Django's User model via user_id.
    """
    user_id = fields.IntField(required=True, unique=True)
    username = fields.StringField(required=True, unique=True, max_length=150)
    email = fields.EmailField(required=True)

    # Profile information
    height = fields.IntField(help_text='Height in centimeters')
    weight = fields.DecimalField(precision=2, help_text='Weight in kilograms')
    date_of_birth = fields.DateTimeField()

    # Fitness preferences
    FITNESS_GOAL_CHOICES = (
        ('strength', 'Strength Training'),
        ('cardio', 'Cardiovascular Health'),
        ('weight_loss', 'Weight Loss'),
        ('weight_gain', 'Weight Gain'),
        ('endurance', 'Endurance'),
        ('flexibility', 'Flexibility'),
        ('general', 'General Fitness'),
    )
    fitness_goal = fields.StringField(choices=FITNESS_GOAL_CHOICES, default='general')

    # Timestamps
    created_at = fields.DateTimeField(default=datetime.utcnow)
    updated_at = fields.DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'user_profiles',
        'indexes': [
            'user_id',
            'username',
            'email',
        ]
    }

    def __str__(self):
        return f"Profile: {self.username}"

    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)


class Exercise(Document):
    """
    Exercise library - contains all available exercises.
    """
    CATEGORY_CHOICES = (
        ('strength', 'Strength'),
        ('cardio', 'Cardio'),
        ('flexibility', 'Flexibility'),
        ('balance', 'Balance'),
        ('plyometric', 'Plyometric'),
        ('olympic', 'Olympic Lifting'),
        ('powerlifting', 'Powerlifting'),
    )

    DIFFICULTY_CHOICES = (
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    )

    name = fields.StringField(required=True, unique=True, max_length=200)
    description = fields.StringField(required=True)
    category = fields.StringField(required=True, choices=CATEGORY_CHOICES)

    # Metadata
    muscle_groups = fields.ListField(fields.StringField(max_length=50))  # e.g., ['chest', 'triceps']
    equipment_required = fields.ListField(fields.StringField(max_length=50))  # e.g., ['barbell', 'bench']
    difficulty = fields.StringField(required=True, choices=DIFFICULTY_CHOICES)

    # Media
    video_url = fields.URLField()
    image_url = fields.URLField()

    # Instructions
    instructions = fields.ListField(fields.StringField())  # Step-by-step instructions

    # Timestamps
    created_at = fields.DateTimeField(default=datetime.utcnow)
    updated_at = fields.DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'exercises',
        'indexes': [
            'name',
            'category',
            'difficulty',
            ('category', 'difficulty'),
        ]
    }

    def __str__(self):
        return f"{self.name} ({self.category})"

    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)


class WorkoutExercise(EmbeddedDocument):
    """
    Embedded document representing an exercise within a workout.
    This is not a standalone collection, but embedded in Workout.
    """
    exercise = fields.ReferenceField(Exercise, required=True)
    order = fields.IntField(required=True, min_value=1)

    # Sets and reps
    sets = fields.IntField(default=3, min_value=1)
    reps = fields.IntField(min_value=1)  # Optional - for counted exercises
    duration = fields.IntField(min_value=1)  # Optional - for timed exercises (seconds)

    # Rest period between sets
    rest_period = fields.IntField(default=60, help_text='Rest period in seconds')

    # Additional notes
    notes = fields.StringField()

    def __str__(self):
        return f"{self.exercise.name} - {self.sets}x{self.reps or 'timed'}"


class Workout(Document):
    """
    Workout template/plan containing multiple exercises.
    Can be created by users and shared publicly.
    """
    title = fields.StringField(required=True, max_length=200)
    description = fields.StringField(required=True)

    # Creator - reference to UserProfile
    creator = fields.ReferenceField(UserProfile, required=True)

    # Visibility
    is_public = fields.BooleanField(default=False)

    # Exercises in this workout (embedded documents)
    exercises = fields.ListField(fields.EmbeddedDocumentField(WorkoutExercise))

    # Workout metadata
    estimated_duration = fields.IntField(help_text='Estimated duration in minutes')

    DIFFICULTY_CHOICES = (
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    )
    difficulty = fields.StringField(required=True, choices=DIFFICULTY_CHOICES)

    # Tags for categorization
    tags = fields.ListField(fields.StringField(max_length=50))  # e.g., ['upper_body', 'hypertrophy']

    # Timestamps
    created_at = fields.DateTimeField(default=datetime.utcnow)
    updated_at = fields.DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'workouts',
        'indexes': [
            'creator',
            'is_public',
            'difficulty',
            'tags',
            '-created_at',  # Descending order for recent workouts
        ]
    }

    def __str__(self):
        return f"{self.title} by {self.creator.username}"

    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)

    def get_total_exercises(self):
        """Return the total number of exercises in this workout."""
        return len(self.exercises)

    def calculate_estimated_duration(self):
        """Calculate estimated duration based on exercises."""
        if not self.exercises:
            return 0

        total_seconds = 0
        for workout_exercise in self.exercises:
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


class WorkoutSession(Document):
    """
    An actual instance of a workout being performed or planned.
    Tracks when a user does a specific workout.
    """
    STATUS_CHOICES = (
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('skipped', 'Skipped'),
        ('cancelled', 'Cancelled'),
    )

    user = fields.ReferenceField(UserProfile, required=True)
    workout = fields.ReferenceField(Workout, required=True)

    status = fields.StringField(required=True, choices=STATUS_CHOICES, default='planned')

    # Scheduling
    scheduled_date = fields.DateTimeField()
    started_at = fields.DateTimeField()
    completed_at = fields.DateTimeField()

    # User notes
    notes = fields.StringField()

    # Timestamps
    created_at = fields.DateTimeField(default=datetime.utcnow)
    updated_at = fields.DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'workout_sessions',
        'indexes': [
            'user',
            'workout',
            'status',
            '-created_at',
            ('user', 'status'),
            ('user', '-completed_at'),
        ]
    }

    def __str__(self):
        return f"{self.user.username} - {self.workout.title} ({self.status})"

    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)

    def start_session(self):
        """Mark session as started."""
        self.status = 'in_progress'
        self.started_at = datetime.utcnow()
        self.save()

    def complete_session(self):
        """Mark session as completed."""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        self.save()

    def get_duration(self):
        """Get actual duration of the session in minutes."""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds() // 60
        return None


class ExerciseLog(Document):
    """
    Log of individual exercise performance within a workout session.
    Tracks actual sets, reps, weight, etc.
    """
    session = fields.ReferenceField(WorkoutSession, required=True)
    exercise = fields.ReferenceField(Exercise, required=True)

    # Set information
    set_number = fields.IntField(required=True, min_value=1)

    # Performance data
    reps = fields.IntField(min_value=0)  # Actual reps completed
    weight = fields.DecimalField(precision=2, min_value=0)  # Weight in kg
    duration = fields.IntField(min_value=0)  # Duration in seconds (for timed exercises)
    distance = fields.DecimalField(precision=2, min_value=0)  # Distance in km (for cardio)

    # Notes for this specific set
    notes = fields.StringField()

    # Perceived difficulty (1-10 scale)
    perceived_exertion = fields.IntField(min_value=1, max_value=10)

    # Timestamp
    created_at = fields.DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'exercise_logs',
        'indexes': [
            'session',
            'exercise',
            'created_at',
            ('session', 'exercise'),
            ('exercise', '-created_at'),  # For exercise history
        ]
    }

    def __str__(self):
        return f"{self.exercise.name} - Set {self.set_number}: {self.reps}x{self.weight}kg"
