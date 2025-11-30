# Interactive Demo Guide

## Overview

`interactive_demo.py` is an interactive Python script that demonstrates the complete Workout API functionality through a guided user scenario. It allows you to interact with all API endpoints through a command-line interface.

## Features

### Guided Demo Mode (Default)
A step-by-step walkthrough of a typical user journey:

1. **Authentication**
   - User registration with profile setup
   - Login for existing users
   - View user profile

2. **Exercise Management**
   - Create sample exercises (Bench Press, Squats, Pull-ups)
   - List and filter exercises
   - Search exercises by name/muscle group

3. **Workout Creation**
   - Build custom workouts from exercises
   - Configure sets, reps, and rest periods
   - Set workout difficulty and goals

4. **Workout Session**
   - Schedule a workout session
   - Start the session (timer begins)
   - Log exercise performance (sets, reps, weights)
   - Complete the session

### Custom Interactive Mode
A menu-driven interface for free exploration:
- Profile management
- Exercise library browsing
- Workout creation and management
- Session tracking
- Exercise log viewing

## Prerequisites

### 1. API Server Running

Make sure the Django API server is running:

```bash
# Activate virtual environment
source venv/bin/activate

# Start development server
python manage.py runserver
```

The API should be accessible at `http://localhost:8000/api/`

### 2. Required Python Packages

Install the requests library if not already installed:

```bash
pip install requests
```

## Usage

### Quick Start - Guided Demo

Run the default guided demo:

```bash
python interactive_demo.py
```

Or make it executable and run directly:

```bash
chmod +x interactive_demo.py
./interactive_demo.py
```

### Custom Interactive Mode

For free exploration with menu-driven interface:

```bash
python interactive_demo.py --custom
```

### Custom API URL

If your API is running on a different host/port:

```bash
python interactive_demo.py --url http://api.example.com/api/
```

### Command-Line Options

```bash
python interactive_demo.py --help

usage: interactive_demo.py [-h] [--url URL] [--custom]

Workout API Interactive Demo

optional arguments:
  -h, --help  show this help message and exit
  --url URL   API base URL (default: http://localhost:8000/api/)
  --custom    Run in custom interactive mode instead of guided demo
```

## Demo Walkthrough

### Step 1: Health Check

The script automatically checks if the API is running:

```
╔══════════════════════════════════════════════════════════════╗
║          HEALTH CHECK                                        ║
╚══════════════════════════════════════════════════════════════╝

Request: GET health/
Status: 200 OK
✅ API is healthy!
```

### Step 2: User Registration

Create a new user account with profile information:

```
╔══════════════════════════════════════════════════════════════╗
║          USER REGISTRATION                                   ║
╚══════════════════════════════════════════════════════════════╝

Let's create a new user account!

Username [demo_user]: john_doe
Email [john_doe@example.com]: john@example.com
Password [SecurePass123!]:
First Name [Demo]: John
Last Name [User]: Doe

Optional profile information:
Height (cm) [175]: 180
Weight (kg) [75]: 80

Fitness goals: weight_loss, muscle_gain, endurance, general
Fitness Goal [muscle_gain]:

✅ Successfully registered as john_doe!
🔑 Authentication token obtained
```

### Step 3: Create Exercises

Add exercises to your library:

```
╔══════════════════════════════════════════════════════════════╗
║          CREATE EXERCISES                                    ║
╚══════════════════════════════════════════════════════════════╝

Let's create some exercises for your workout library!

Exercise 1/3: Barbell Bench Press
Create this exercise? (y/n): y

Request: POST exercises/
Status: 201 Created
✅ Created: Barbell Bench Press

Exercise 2/3: Barbell Squat
Create this exercise? (y/n): y
✅ Created: Barbell Squat

Exercise 3/3: Pull-ups
Create this exercise? (y/n): y
✅ Created: Pull-ups

✅ Created 3 exercises
```

### Step 4: Build a Workout

Create a custom workout:

```
╔══════════════════════════════════════════════════════════════╗
║          CREATE WORKOUT                                      ║
╚══════════════════════════════════════════════════════════════╝

Let's create a workout!

Workout name [Push Day A]:
Description [Chest, shoulders, triceps]:
Difficulty [intermediate]:
Estimated duration (minutes) [60]:
Goal [muscle_gain]:

📋 Available exercises (3):
1. Barbell Bench Press
2. Barbell Squat
3. Pull-ups

Select exercises to add (enter numbers separated by commas, e.g., 1,2,3): 1,3

📌 Exercise: Barbell Bench Press
  Sets [3]: 4
  Reps [10]: 8
  Rest period (seconds) [60]: 90

📌 Exercise: Pull-ups
  Sets [3]:
  Reps [10]:
  Rest period (seconds) [60]:

✅ Workout created successfully!
```

### Step 5: Start a Session

Create and start a workout session:

```
╔══════════════════════════════════════════════════════════════╗
║          CREATE WORKOUT SESSION                              ║
╚══════════════════════════════════════════════════════════════╝

Available workouts:
1. Push Day A - 60 min

Select workout (1-1) [1]:

Scheduling: Push Day A
Schedule for now? (y/n): y

✅ Session created successfully!

╔══════════════════════════════════════════════════════════════╗
║          START WORKOUT SESSION                               ║
╚══════════════════════════════════════════════════════════════╝

Starting session: 692c6d8f...

✅ Session started!
⏱️  Timer started at: 2024-11-30T16:30:00Z
```

### Step 6: Log Exercise Performance

Log your performance for each exercise:

```
╔══════════════════════════════════════════════════════════════╗
║          LOG EXERCISE PERFORMANCE                            ║
╚══════════════════════════════════════════════════════════════╝

============================================================
Exercise 1/2: Barbell Bench Press
Planned: 4 sets × 8 reps
============================================================

Log this exercise? (y/n): y
Sets completed [4]:
Enter reps for each of 4 sets:
  Set 1 reps [8]:
  Set 2 reps [8]:
  Set 3 reps [8]: 7
  Set 4 reps [8]: 6

Log weights? (y/n): y
Enter weight for each set (kg):
  Set 1 weight [0]: 100
  Set 2 weight [0]: 100
  Set 3 weight [0]: 100
  Set 4 weight [0]: 100

Notes (optional): Felt strong today!

✅ Logged Barbell Bench Press

============================================================
Exercise 2/2: Pull-ups
Planned: 3 sets × 10 reps
============================================================

Log this exercise? (y/n): y
[... similar logging ...]

✅ Logged 2/2 exercises
```

### Step 7: Complete the Session

Finish your workout:

```
╔══════════════════════════════════════════════════════════════╗
║          COMPLETE WORKOUT SESSION                            ║
╚══════════════════════════════════════════════════════════════╝

Completing session: 692c6d8f...

Actual duration (minutes) [60]: 65
Session notes [Great workout!]: Pushed hard on the bench!

✅ Session completed!
🎉 Great job!
```

### Step 8: Demo Complete

```
╔══════════════════════════════════════════════════════════════╗
║          DEMO COMPLETE                                       ║
╚══════════════════════════════════════════════════════════════╝

✅ Demo completed successfully!

You've experienced the complete workout tracking flow:
- ✅ User authentication
- ✅ Exercise library management
- ✅ Workout creation
- ✅ Session tracking
- ✅ Performance logging

Thank you for trying the Workout API! 🎉
```

## Custom Mode Features

When running with `--custom` flag, you get a menu-driven interface:

```
============================================================
MAIN MENU
============================================================
1. View Profile
2. Manage Exercises
3. Manage Workouts
4. Manage Sessions
5. View Exercise Logs
0. Exit
============================================================
Select option:
```

### Menu Options

#### 1. View Profile
- Displays current user information
- Shows profile data from MongoDB

#### 2. Manage Exercises
- List all exercises (with filtering)
- Create new exercises
- Search exercises by name, muscle group, equipment

#### 3. Manage Workouts
- List all workouts
- Create new workout from exercises
- View workout details

#### 4. Manage Sessions
- Create workout session
- Start session
- Complete session
- Requires session ID input

#### 5. View Exercise Logs
- Lists all exercise logs
- Shows performance history

## Sample Input/Output

### Example Request Display

```
============================================================
Request: POST exercises/
Payload: {
  "name": "Barbell Bench Press",
  "description": "Classic chest exercise using barbell",
  "muscle_group": "chest",
  "equipment": "barbell",
  "difficulty": "intermediate",
  "instructions": "1. Lie on bench\n2. Lower bar to chest\n3. Press up"
}
Status: 201 Created
============================================================

Response:
{
  "id": "692c6d8fc5a8a9e9130c4713",
  "name": "Barbell Bench Press",
  "description": "Classic chest exercise using barbell",
  "muscle_group": "chest",
  "equipment": "barbell",
  "difficulty": "intermediate",
  "instructions": "1. Lie on bench\n2. Lower bar to chest\n3. Press up",
  "created_by": "692c6ca3c5a8a9e9130c4712",
  "is_public": false,
  "created_at": "2024-11-30T16:25:00Z"
}
```

## Tips for Best Experience

### 1. Use Default Values

The script provides sensible defaults for most inputs. Simply press Enter to accept them:

```
Username [demo_user]:           # Press Enter to use "demo_user"
Height (cm) [175]: 180          # Or type custom value
```

### 2. Follow the Prompts

Each step has clear instructions and examples:

```
Fitness goals: weight_loss, muscle_gain, endurance, general
Fitness Goal [muscle_gain]:
```

### 3. Skip Optional Steps

You can skip optional features:

```
Filter by muscle group? (y/n): n    # Skip filtering
```

### 4. Interrupt Anytime

Press `Ctrl+C` to safely exit:

```
^C
👋 Demo interrupted. Goodbye!
```

## Troubleshooting

### API Connection Error

```
❌ Error: ('Connection aborted.', ConnectionRefusedError(...))
```

**Solution**: Make sure the API server is running:
```bash
python manage.py runserver
```

### Authentication Errors

```
❌ Registration failed!
Error Response:
{
  "error": "Username already exists"
}
```

**Solution**: Use a different username or login with existing account

### Invalid Input

```
❌ Failed to create exercise
Error Response:
{
  "muscle_group": ["Invalid choice: 'invalid_muscle'"]
}
```

**Solution**: Check the valid options listed in prompts

### MongoDB/Database Errors

```
❌ Failed to create workout
{
  "error": "Could not save document..."
}
```

**Solution**:
- Check MongoDB connection
- Ensure port-forward is active: `kubectl -n woodez-database port-forward mongodb-1 27012:27017`
- Verify PostgreSQL is running

## Advanced Usage

### Testing Different Scenarios

#### Test Registration Flow

```bash
# Run demo, choose new account
python interactive_demo.py
# Answer "n" to "Do you have an existing account?"
```

#### Test Login Flow

```bash
# Run demo, use existing account
python interactive_demo.py
# Answer "y" to "Do you have an existing account?"
```

#### Test Filtering

```bash
# Use custom mode for fine-grained control
python interactive_demo.py --custom
# Choose "2. Manage Exercises"
# Choose "3. Search exercises"
# Apply filters for muscle group, equipment, etc.
```

### Integration with Test Suite

The script can be used to:
- Manually verify API endpoints
- Generate test data
- Validate end-to-end workflows
- Demonstrate API capabilities

### Extending the Script

The `WorkoutAPIDemo` class is modular and can be extended:

```python
from interactive_demo import WorkoutAPIDemo

# Create custom demo
demo = WorkoutAPIDemo(base_url="http://localhost:8000/api/")

# Add custom methods
demo.custom_workflow()
```

## Code Structure

### Main Components

```
WorkoutAPIDemo
├── __init__()              # Initialize with API URL
├── Authentication
│   ├── register_user()     # Register new user
│   ├── login_user()        # Login existing user
│   └── get_current_user()  # Get profile
├── Exercises
│   ├── create_exercises()  # Create sample exercises
│   └── list_exercises()    # List/search exercises
├── Workouts
│   ├── create_workout()    # Build workout
│   └── list_workouts()     # List workouts
├── Sessions
│   ├── create_session()    # Schedule session
│   ├── start_session()     # Start workout
│   ├── log_exercise()      # Log performance
│   └── complete_session()  # Finish workout
└── Main Flows
    ├── run_demo()          # Guided demo
    └── run_custom()        # Interactive menu
```

### Helper Methods

- `_make_request()` - HTTP request wrapper with logging
- `_headers()` - Authentication header management
- `print_header()` - Section formatting
- `print_response()` - Pretty-print JSON
- `get_input()` - User input with defaults
- `confirm()` - Yes/no prompts
- `wait_for_continue()` - Pause for user

## Performance Considerations

- API requests have 10-second timeout
- Session management with `requests.Session()` for connection pooling
- Automatic token management (stored after login/registration)
- Graceful error handling with detailed error messages

## Security Notes

- Passwords are entered in plain text (suitable for demo only)
- Tokens displayed in output (demo purposes)
- For production use, implement secure credential management

## Next Steps

After running the demo:

1. **Explore the API**: Use the custom mode to try different features
2. **Check the database**: Verify data was stored in MongoDB/PostgreSQL
3. **Review logs**: Check Django server output for request details
4. **Run automated tests**: `pytest` for comprehensive testing
5. **Try the API directly**: Use Postman or curl with the knowledge gained

## Support

For issues or questions:
- Check the API logs: Django console output
- Review TEST_PLAN.md for detailed test scenarios
- Consult API documentation (if available)
- Check CLAUDE.md for project setup instructions

---

**Happy Testing! 🏋️**
