import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

def print_step(step_name):
    print(f"\n{'='*20} {step_name} {'='*20}")

def print_response(response):
    print(f"Status Code: {response.status_code}")
    try:
        print("Response:", json.dumps(response.json(), indent=2))
    except:
        print("Response:", response.text)
    
    if 200 <= response.status_code < 300:
        print("✅ SUCCESS")
    else:
        print("❌ FAILED")
        sys.exit(1)

def test_api_flow():
    # 1. Create User
    print_step("1. Creating New User")
    user_name = f"Test User {datetime.now().strftime('%H%M%S')}"
    payload = {
        "name": user_name,
        "email": f"test{datetime.now().strftime('%H%M%S')}@example.com"
    }
    response = requests.post(f"{BASE_URL}/users", json=payload)
    print_response(response)
    user_id = response.json()['data']['id']

    # 2. Start Workout
    print_step("2. Starting Workout Session")
    payload = {
        "assigned_reps": 10,
        "exercise_name": "Push-ups"
    }
    response = requests.post(f"{BASE_URL}/users/{user_id}/workouts", json=payload)
    print_response(response)
    session_id = response.json()['data']['id']

    # 3. Log Exercise (Complete all reps)
    print_step("3. Logging Exercise (10/10 reps)")
    payload = {
        "completed_reps": 10
    }
    response = requests.patch(f"{BASE_URL}/workouts/{session_id}/log", json=payload)
    print_response(response)

    # 4. End Workout
    print_step("4. Ending Workout Session")
    response = requests.patch(f"{BASE_URL}/workouts/{session_id}/end")
    print_response(response)
    
    # Verify logic
    next_reps = response.json()['data']['summary']['next_recommended_reps']
    print(f"\nLogic Check: Completed 10/10 reps. Next recommended: {next_reps}")
    if next_reps == 12:
        print("✅ ALGORITHM VERIFIED (10 + 2 = 12)")
    else:
        print(f"❌ ALGORITHM FAILED (Expected 12, got {next_reps})")

    # 5. Get Recommendation
    print_step("5. Fetching Recommendation")
    response = requests.get(f"{BASE_URL}/users/{user_id}/recommendations")
    print_response(response)

if __name__ == "__main__":
    try:
        test_api_flow()
        print("\n✨ ALL API TESTS PASSED SUCCESSFULLY! ✨")
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to server. Is it running on http://localhost:8000?")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
