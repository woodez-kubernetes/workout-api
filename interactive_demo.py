#!/usr/bin/env python
"""
Interactive Workout API Demo Script

This script walks through a typical user scenario with the Workout API,
allowing users to interact with various endpoints through a CLI interface.

Usage:
    python interactive_demo.py

Requirements:
    - API server running on localhost:8000
    - requests library installed
"""

import requests
import json
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import time


class WorkoutAPIDemo:
    """Interactive demo client for Workout API."""

    def __init__(self, base_url: str = "http://localhost:8000/api/"):
        self.base_url = base_url
        self.token: Optional[str] = None
        self.user_data: Optional[Dict[str, Any]] = None
        self.session = requests.Session()

    def _headers(self) -> Dict[str, str]:
        """Get request headers with authentication token."""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Token {self.token}"
        return headers

    def _make_request(
        self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to API."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=self._headers(),
                timeout=10
            )

            print(f"\n{'='*60}")
            print(f"Request: {method} {endpoint}")
            if data:
                print(f"Payload: {json.dumps(data, indent=2)}")
            print(f"Status: {response.status_code} {response.reason}")
            print(f"{'='*60}")

            if response.status_code == 204:
                return {"status": "success", "message": "No content"}

            try:
                return response.json()
            except json.JSONDecodeError:
                return {"status": response.status_code, "text": response.text}
        except requests.exceptions.RequestException as e:
            print(f"\n❌ Error: {e}")
            return {"error": str(e)}

    def print_header(self, title: str):
        """Print section header."""
        print(f"\n{'#'*60}")
        print(f"# {title}")
        print(f"{'#'*60}\n")

    def print_response(self, response: Dict[str, Any], title: str = "Response"):
        """Print formatted response."""
        print(f"\n{title}:")
        print(json.dumps(response, indent=2, default=str))

    def get_input(self, prompt: str, default: Optional[str] = None) -> str:
        """Get user input with optional default value."""
        if default:
            user_input = input(f"{prompt} [{default}]: ").strip()
            return user_input if user_input else default
        return input(f"{prompt}: ").strip()

    def confirm(self, message: str) -> bool:
        """Ask for yes/no confirmation."""
        response = input(f"{message} (y/n): ").strip().lower()
        return response in ['y', 'yes']

    def wait_for_continue(self):
        """Wait for user to press enter."""
        input("\nPress Enter to continue...")

    # ========================================================================
    # Authentication Flow
    # ========================================================================

    def register_user(self):
        """Register a new user."""
        self.print_header("USER REGISTRATION")

        print("Let's create a new user account!\n")

        username = self.get_input("Username", "demo_user")
        email = self.get_input("Email", f"{username}@example.com")
        password = self.get_input("Password", "SecurePass123!")
        first_name = self.get_input("First Name", "Demo")
        last_name = self.get_input("Last Name", "User")

        print("\nOptional profile information:")
        height = self.get_input("Height (cm)", "175")
        weight = self.get_input("Weight (kg)", "75")

        print("\nFitness goals: weight_loss, muscle_gain, endurance, general")
        fitness_goal = self.get_input("Fitness Goal", "muscle_gain")

        data = {
            "username": username,
            "email": email,
            "password": password,
            "password_confirm": password,
            "first_name": first_name,
            "last_name": last_name,
            "height": int(height) if height else None,
            "weight": float(weight) if weight else None,
            "fitness_goal": fitness_goal
        }

        response = self._make_request("POST", "auth/register/", data)

        if "token" in response:
            self.token = response["token"]
            self.user_data = response.get("user", {})
            print(f"\n✅ Successfully registered as {username}!")
            print(f"🔑 Authentication token obtained")
            self.print_response(response, "Registration Response")
        else:
            print(f"\n❌ Registration failed!")
            self.print_response(response, "Error Response")

        self.wait_for_continue()
        return "token" in response

    def login_user(self):
        """Login existing user."""
        self.print_header("USER LOGIN")

        username = self.get_input("Username")
        password = self.get_input("Password")

        data = {
            "username": username,
            "password": password
        }

        response = self._make_request("POST", "auth/login/", data)

        if "token" in response:
            self.token = response["token"]
            self.user_data = response.get("user", {})
            print(f"\n✅ Successfully logged in as {username}!")
            self.print_response(response, "Login Response")
        else:
            print(f"\n❌ Login failed!")
            self.print_response(response, "Error Response")

        self.wait_for_continue()
        return "token" in response

    def get_current_user(self):
        """Get current user profile."""
        self.print_header("GET CURRENT USER PROFILE")

        response = self._make_request("GET", "auth/me/")
        self.print_response(response)
        self.wait_for_continue()

    # ========================================================================
    # Exercise Management
    # ========================================================================

    def create_exercises(self):
        """Create sample exercises."""
        self.print_header("CREATE EXERCISES")

        print("Let's create some exercises for your workout library!\n")

        sample_exercises = [
            {
                "name": "Barbell Bench Press",
                "description": "Classic chest exercise using barbell",
                "muscle_group": "chest",
                "equipment": "barbell",
                "difficulty": "intermediate",
                "instructions": "1. Lie on bench\n2. Lower bar to chest\n3. Press up"
            },
            {
                "name": "Barbell Squat",
                "description": "Compound leg exercise",
                "muscle_group": "legs",
                "equipment": "barbell",
                "difficulty": "intermediate",
                "instructions": "1. Bar on shoulders\n2. Lower to parallel\n3. Stand up"
            },
            {
                "name": "Pull-ups",
                "description": "Bodyweight back exercise",
                "muscle_group": "back",
                "equipment": "bodyweight",
                "difficulty": "intermediate",
                "instructions": "1. Hang from bar\n2. Pull chin over bar\n3. Lower down"
            }
        ]

        created_exercises = []

        for i, exercise_data in enumerate(sample_exercises, 1):
            print(f"\nExercise {i}/{len(sample_exercises)}: {exercise_data['name']}")

            if self.confirm("Create this exercise?"):
                response = self._make_request("POST", "exercises/", exercise_data)

                if response.get("id"):
                    print(f"✅ Created: {exercise_data['name']}")
                    created_exercises.append(response)
                else:
                    print(f"❌ Failed to create exercise")
                    self.print_response(response)
            else:
                print("Skipped.")

        print(f"\n✅ Created {len(created_exercises)} exercises")
        self.wait_for_continue()
        return created_exercises

    def list_exercises(self):
        """List available exercises."""
        self.print_header("LIST EXERCISES")

        params = {}

        if self.confirm("Filter by muscle group?"):
            print("Options: chest, back, legs, shoulders, arms, core, full_body")
            muscle_group = self.get_input("Muscle group")
            if muscle_group:
                params["muscle_group"] = muscle_group

        if self.confirm("Filter by equipment?"):
            print("Options: barbell, dumbbell, machine, bodyweight, cable, other")
            equipment = self.get_input("Equipment")
            if equipment:
                params["equipment"] = equipment

        if self.confirm("Search by name?"):
            search = self.get_input("Search term")
            if search:
                params["search"] = search

        response = self._make_request("GET", "exercises/", params=params)

        if "results" in response:
            exercises = response["results"]
            print(f"\n📋 Found {len(exercises)} exercises:")
            for i, ex in enumerate(exercises[:10], 1):  # Show first 10
                print(f"\n{i}. {ex.get('name', 'Unknown')}")
                print(f"   Muscle: {ex.get('muscle_group', 'N/A')} | "
                      f"Equipment: {ex.get('equipment', 'N/A')} | "
                      f"Difficulty: {ex.get('difficulty', 'N/A')}")
        else:
            self.print_response(response)

        self.wait_for_continue()
        return response.get("results", [])

    # ========================================================================
    # Workout Management
    # ========================================================================

    def create_workout(self, exercises: list):
        """Create a workout from exercises."""
        self.print_header("CREATE WORKOUT")

        if not exercises:
            print("No exercises available. Creating some first...")
            exercises = self.create_exercises()

        if not exercises:
            print("❌ Cannot create workout without exercises")
            self.wait_for_continue()
            return None

        print("Let's create a workout!\n")

        name = self.get_input("Workout name", "Push Day A")
        description = self.get_input("Description", "Chest, shoulders, triceps")

        print("\nDifficulty levels: beginner, intermediate, advanced")
        difficulty = self.get_input("Difficulty", "intermediate")

        duration = self.get_input("Estimated duration (minutes)", "60")

        print("\nGoals: muscle_gain, weight_loss, endurance, strength, general")
        goal = self.get_input("Goal", "muscle_gain")

        # Select exercises for workout
        print(f"\n📋 Available exercises ({len(exercises)}):")
        for i, ex in enumerate(exercises, 1):
            print(f"{i}. {ex.get('name', 'Unknown')}")

        workout_exercises = []
        print("\nSelect exercises to add (enter numbers separated by commas, e.g., 1,2,3):")
        selection = self.get_input("Exercise numbers", "1,2,3")

        selected_indices = [int(x.strip()) - 1 for x in selection.split(",") if x.strip().isdigit()]

        for order, idx in enumerate(selected_indices, 1):
            if 0 <= idx < len(exercises):
                exercise = exercises[idx]
                print(f"\n📌 Exercise: {exercise.get('name')}")
                sets = int(self.get_input("  Sets", "3"))
                reps = int(self.get_input("  Reps", "10"))
                rest = int(self.get_input("  Rest period (seconds)", "60"))

                workout_exercises.append({
                    "exercise_id": exercise.get("id"),
                    "sets": sets,
                    "reps": reps,
                    "rest_period": rest,
                    "order": order
                })

        data = {
            "name": name,
            "description": description,
            "difficulty": difficulty,
            "estimated_duration": int(duration),
            "goal": goal,
            "exercises": workout_exercises
        }

        response = self._make_request("POST", "workouts/", data)

        if response.get("id"):
            print(f"\n✅ Workout created successfully!")
            self.print_response(response)
        else:
            print(f"\n❌ Failed to create workout")
            self.print_response(response)

        self.wait_for_continue()
        return response if response.get("id") else None

    def list_workouts(self):
        """List user's workouts."""
        self.print_header("LIST WORKOUTS")

        response = self._make_request("GET", "workouts/")

        if "results" in response:
            workouts = response["results"]
            print(f"\n📋 Found {len(workouts)} workouts:")
            for i, wo in enumerate(workouts, 1):
                print(f"\n{i}. {wo.get('name', 'Unknown')}")
                print(f"   {wo.get('description', '')}")
                print(f"   Difficulty: {wo.get('difficulty', 'N/A')} | "
                      f"Duration: {wo.get('estimated_duration', 'N/A')} min | "
                      f"Exercises: {len(wo.get('exercises', []))}")
        else:
            self.print_response(response)

        self.wait_for_continue()
        return response.get("results", [])

    # ========================================================================
    # Workout Session Management
    # ========================================================================

    def create_session(self, workouts: list):
        """Create a workout session."""
        self.print_header("CREATE WORKOUT SESSION")

        if not workouts:
            print("No workouts available. Please create a workout first.")
            self.wait_for_continue()
            return None

        print("Available workouts:")
        for i, wo in enumerate(workouts, 1):
            print(f"{i}. {wo.get('name')} - {wo.get('estimated_duration')} min")

        selection = int(self.get_input(f"Select workout (1-{len(workouts)})", "1")) - 1

        if 0 <= selection < len(workouts):
            workout = workouts[selection]

            print(f"\nScheduling: {workout.get('name')}")

            if self.confirm("Schedule for now?"):
                scheduled_date = datetime.now().isoformat()
            else:
                date_str = self.get_input("Date/time (YYYY-MM-DD HH:MM)",
                                         (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d 10:00"))
                try:
                    scheduled_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M").isoformat()
                except ValueError:
                    scheduled_date = datetime.now().isoformat()

            notes = self.get_input("Notes (optional)", "")

            data = {
                "workout_id": workout.get("id"),
                "scheduled_date": scheduled_date,
                "notes": notes
            }

            response = self._make_request("POST", "sessions/", data)

            if response.get("id"):
                print(f"\n✅ Session created successfully!")
                self.print_response(response)
            else:
                print(f"\n❌ Failed to create session")
                self.print_response(response)

            self.wait_for_continue()
            return response if response.get("id") else None

        return None

    def start_session(self, session_id: str):
        """Start a workout session."""
        self.print_header("START WORKOUT SESSION")

        print(f"Starting session: {session_id}\n")

        response = self._make_request("POST", f"sessions/{session_id}/start/")

        if response.get("status") == "in_progress":
            print(f"\n✅ Session started!")
            print(f"⏱️  Timer started at: {response.get('started_at')}")
            self.print_response(response)
        else:
            print(f"\n❌ Failed to start session")
            self.print_response(response)

        self.wait_for_continue()
        return response

    def log_exercise(self, session_id: str, workout: dict):
        """Log exercise performance during session."""
        self.print_header("LOG EXERCISE PERFORMANCE")

        exercises = workout.get("exercises", [])

        if not exercises:
            print("No exercises in this workout")
            self.wait_for_continue()
            return []

        logged = []

        for i, workout_exercise in enumerate(exercises, 1):
            exercise_name = workout_exercise.get("exercise", {}).get("name", "Unknown")
            planned_sets = workout_exercise.get("sets", 0)
            planned_reps = workout_exercise.get("reps", 0)

            print(f"\n{'='*60}")
            print(f"Exercise {i}/{len(exercises)}: {exercise_name}")
            print(f"Planned: {planned_sets} sets × {planned_reps} reps")
            print(f"{'='*60}")

            if not self.confirm("Log this exercise?"):
                print("Skipped.")
                continue

            sets_completed = int(self.get_input(f"Sets completed", str(planned_sets)))

            # Get reps for each set
            reps_completed = []
            print(f"\nEnter reps for each of {sets_completed} sets:")
            for set_num in range(sets_completed):
                reps = int(self.get_input(f"  Set {set_num + 1} reps", str(planned_reps)))
                reps_completed.append(reps)

            # Get weights for each set
            if self.confirm("Log weights?"):
                weight = []
                print(f"\nEnter weight for each set (kg):")
                for set_num in range(sets_completed):
                    w = float(self.get_input(f"  Set {set_num + 1} weight", "0"))
                    weight.append(w)
            else:
                weight = []

            notes = self.get_input("Notes (optional)", "")

            data = {
                "session_id": session_id,
                "exercise_id": workout_exercise.get("exercise", {}).get("id"),
                "sets_completed": sets_completed,
                "reps_completed": reps_completed,
                "weight": weight,
                "notes": notes
            }

            response = self._make_request("POST", "logs/", data)

            if response.get("id"):
                print(f"\n✅ Logged {exercise_name}")
                logged.append(response)
            else:
                print(f"\n❌ Failed to log exercise")
                self.print_response(response)

        print(f"\n✅ Logged {len(logged)}/{len(exercises)} exercises")
        self.wait_for_continue()
        return logged

    def complete_session(self, session_id: str):
        """Complete a workout session."""
        self.print_header("COMPLETE WORKOUT SESSION")

        print(f"Completing session: {session_id}\n")

        duration = self.get_input("Actual duration (minutes)", "60")
        notes = self.get_input("Session notes", "Great workout!")

        data = {
            "duration": int(duration),
            "notes": notes
        }

        response = self._make_request("POST", f"sessions/{session_id}/complete/", data)

        if response.get("status") == "completed":
            print(f"\n✅ Session completed!")
            print(f"🎉 Great job!")
            self.print_response(response)
        else:
            print(f"\n❌ Failed to complete session")
            self.print_response(response)

        self.wait_for_continue()
        return response

    # ========================================================================
    # Main Demo Flow
    # ========================================================================

    def run_demo(self):
        """Run the complete demo scenario."""
        print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║          🏋️  WORKOUT API INTERACTIVE DEMO  🏋️                ║
║                                                              ║
║  This demo will walk you through a typical user scenario:   ║
║  1. Register/Login                                           ║
║  2. Create exercises                                         ║
║  3. Build a workout                                          ║
║  4. Start a workout session                                  ║
║  5. Log exercise performance                                 ║
║  6. Complete the session                                     ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """)

        # Check API health
        self.print_header("HEALTH CHECK")
        health = self._make_request("GET", "health/")
        if health.get("status") != "healthy":
            print("❌ API is not healthy! Please start the server.")
            return
        print("✅ API is healthy!")
        self.wait_for_continue()

        # Authentication
        if self.confirm("Do you have an existing account?"):
            if not self.login_user():
                return
        else:
            if not self.register_user():
                return

        # View profile
        if self.confirm("View your profile?"):
            self.get_current_user()

        # Exercise management
        exercises = []
        if self.confirm("Create sample exercises?"):
            exercises = self.create_exercises()

        if self.confirm("List all exercises?"):
            exercises = self.list_exercises()

        # Workout management
        workouts = []
        if self.confirm("Create a workout?"):
            workout = self.create_workout(exercises)
            if workout:
                workouts = [workout]

        if self.confirm("List all workouts?"):
            workouts = self.list_workouts()

        if not workouts:
            print("\n❌ No workouts available. Exiting demo.")
            return

        # Workout session flow
        if self.confirm("Create and complete a workout session?"):
            # Create session
            session = self.create_session(workouts)

            if session and session.get("id"):
                session_id = session["id"]

                # Start session
                if self.confirm("Start the session now?"):
                    self.start_session(session_id)

                    # Log exercises
                    if self.confirm("Log exercise performance?"):
                        workout = session.get("workout", {})
                        self.log_exercise(session_id, workout)

                    # Complete session
                    if self.confirm("Complete the session?"):
                        self.complete_session(session_id)

        # Summary
        self.print_header("DEMO COMPLETE")
        print("""
✅ Demo completed successfully!

You've experienced the complete workout tracking flow:
- ✅ User authentication
- ✅ Exercise library management
- ✅ Workout creation
- ✅ Session tracking
- ✅ Performance logging

Thank you for trying the Workout API! 🎉
        """)

    def run_custom(self):
        """Run custom interactive mode."""
        print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║          🔧  WORKOUT API CUSTOM MODE  🔧                      ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """)

        # Login first
        if not self.confirm("Do you have an existing account?"):
            if not self.register_user():
                return
        else:
            if not self.login_user():
                return

        while True:
            print("\n" + "="*60)
            print("MAIN MENU")
            print("="*60)
            print("1. View Profile")
            print("2. Manage Exercises")
            print("3. Manage Workouts")
            print("4. Manage Sessions")
            print("5. View Exercise Logs")
            print("0. Exit")
            print("="*60)

            choice = self.get_input("Select option")

            if choice == "1":
                self.get_current_user()
            elif choice == "2":
                self._exercises_menu()
            elif choice == "3":
                self._workouts_menu()
            elif choice == "4":
                self._sessions_menu()
            elif choice == "5":
                self._logs_menu()
            elif choice == "0":
                print("\n👋 Goodbye!")
                break
            else:
                print("Invalid option")

    def _exercises_menu(self):
        """Exercises submenu."""
        print("\n--- EXERCISES MENU ---")
        print("1. List exercises")
        print("2. Create exercises")
        print("3. Search exercises")

        choice = self.get_input("Select option")

        if choice == "1":
            self.list_exercises()
        elif choice == "2":
            self.create_exercises()
        elif choice == "3":
            self.list_exercises()

    def _workouts_menu(self):
        """Workouts submenu."""
        print("\n--- WORKOUTS MENU ---")
        print("1. List workouts")
        print("2. Create workout")

        choice = self.get_input("Select option")

        if choice == "1":
            self.list_workouts()
        elif choice == "2":
            exercises = self.list_exercises()
            self.create_workout(exercises)

    def _sessions_menu(self):
        """Sessions submenu."""
        print("\n--- SESSIONS MENU ---")
        print("1. Create session")
        print("2. Start session")
        print("3. Complete session")

        choice = self.get_input("Select option")

        if choice == "1":
            workouts = self.list_workouts()
            self.create_session(workouts)
        elif choice in ["2", "3"]:
            session_id = self.get_input("Session ID")
            if choice == "2":
                self.start_session(session_id)
            else:
                self.complete_session(session_id)

    def _logs_menu(self):
        """Logs submenu."""
        print("\n--- EXERCISE LOGS MENU ---")
        response = self._make_request("GET", "logs/")
        self.print_response(response)
        self.wait_for_continue()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Workout API Interactive Demo")
    parser.add_argument(
        "--url",
        default="http://localhost:8000/api/",
        help="API base URL (default: http://localhost:8000/api/)"
    )
    parser.add_argument(
        "--custom",
        action="store_true",
        help="Run in custom interactive mode instead of guided demo"
    )

    args = parser.parse_args()

    demo = WorkoutAPIDemo(base_url=args.url)

    try:
        if args.custom:
            demo.run_custom()
        else:
            demo.run_demo()
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
