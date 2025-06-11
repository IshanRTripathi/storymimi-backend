import requests
import json

def test_create_user():
    url = "http://localhost:8000/users/"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "username": "testuser",
        "email": "test@example.com"
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code, response.text
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None, str(e)

if __name__ == "__main__":
    print("Testing user creation endpoint...")
    status_code, response_text = test_create_user()
    
    if status_code and 200 <= status_code < 300:
        print("User created successfully!")
    else:
        print("Failed to create user.")