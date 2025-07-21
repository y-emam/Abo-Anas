import requests
import json

# Base URL of your Flask server
BASE_URL = "http://localhost:5000"

def test_json_post():
    """Test JSON POST request"""
    print("Testing JSON POST request to /api/v1/data...")
    
    test_data = {
        "name": "John Doe",
        "email": "john@example.com",
        "age": 30,
        "message": "Hello from the test client!"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/data",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        print("-" * 50)
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server. Make sure the Flask app is running.")
    except Exception as e:
        print(f"Error: {e}")

def test_echo_post():
    """Test echo POST request"""
    print("Testing echo POST request to /api/v1/echo...")
    
    test_data = {
        "test": "This should be echoed back",
        "number": 42,
        "array": [1, 2, 3, 4, 5]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/echo",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        print("-" * 50)
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server. Make sure the Flask app is running.")
    except Exception as e:
        print(f"Error: {e}")

def test_form_post():
    """Test form data POST request"""
    print("Testing form POST request to /api/v1/form...")
    
    form_data = {
        "username": "testuser",
        "password": "testpass",
        "email": "test@example.com"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/form",
            data=form_data
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        print("-" * 50)
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server. Make sure the Flask app is running.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Flask Server Test Client")
    print("=" * 50)
    print("Make sure your Flask server is running before running these tests!")
    print("Start the server by running: python app.py")
    print("=" * 50)
    
    # Run all tests
    test_json_post()
    test_echo_post()
    test_form_post()
    
    print("All tests completed!")
