import os
import requests
import jwt
import time
import subprocess
import time as t
from backend.config import Config

# Set dummy DB
os.environ['DATABASE_URL'] = 'sqlite:///test.db'

def start_app():
    # Start the app in a separate process
    proc = subprocess.Popen(['python', '-c', "from backend.app import app; app.run(host='0.0.0.0', port=5000, debug=False)"])
    t.sleep(2)  # Wait for app to start
    return proc

def create_token():
    payload = {
        "sub": "1",
        "role": "user",
        "username": "test",
        "email": "test@example.com",
        "exp": int(time.time()) + 3600,
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm=Config.JWT_ALGO)

# Start app
proc = start_app()

try:
    token = create_token()

    # Test 1: Structural Safety Check
    print("Test 1: Structural Safety Check")
    response = requests.get('http://localhost:5000/api/public/ideas')
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

    # Test 2: Authenticated Generation Smoke Test
    print("\nTest 2: Authenticated Generation Smoke Test")
    headers = {'Authorization': f'Bearer {token}'}
    data = {
        "query": "AI tool for code review",
        "domain_id": 1  # Assuming domain 1 exists
    }
    response = requests.post('http://localhost:5000/api/ideas/generate', json=data, headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        resp_data = response.json()
        print(f"Idea: {resp_data.get('idea', {}).get('title')}")
        print(f"Novelty Score: {resp_data.get('novelty_score')}")
        print(f"Evidence Summary: {resp_data.get('evidence_summary')}")
    else:
        print(f"Error: {response.json()}")

finally:
    proc.terminate()
    proc.wait()
