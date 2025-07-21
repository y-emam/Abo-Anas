import requests
import json

# Base URL of your Flask server
BASE_URL = "http://localhost:5000"

def test_voice_endpoint():
    """Test the Twilio voice endpoint"""
    print("Testing Twilio voice endpoint /api/v1/voice...")
    
    # Simulate a Twilio voice request
    # Twilio sends form data, not JSON
    twilio_data = {
        'CallSid': 'CA1234567890abcdef1234567890abcdef',
        'From': '+1234567890',
        'To': '+0987654321',
        'CallStatus': 'in-progress',
        'Direction': 'inbound'
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/voice",
            data=twilio_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print(f"TwiML Response:")
        print(response.text)
        print("-" * 50)
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server. Make sure the Flask app is running.")
    except Exception as e:
        print(f"Error: {e}")

def test_recording_endpoint():
    """Test the recording handler endpoint"""
    print("Testing recording handler endpoint /api/v1/handle-recording...")
    
    # Simulate Twilio recording data
    recording_data = {
        'RecordingUrl': 'https://api.twilio.com/recordings/RE1234567890abcdef.mp3',
        'RecordingSid': 'RE1234567890abcdef',
        'RecordingDuration': '15',
        'CallSid': 'CA1234567890abcdef1234567890abcdef'
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/handle-recording",
            data=recording_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print(f"TwiML Response:")
        print(response.text)
        print("-" * 50)
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server. Make sure the Flask app is running.")
    except Exception as e:
        print(f"Error: {e}")

def test_voice_endpoint_with_curl_command():
    """Print curl commands for testing"""
    print("Curl commands for testing:")
    print("=" * 50)
    
    print("1. Test voice endpoint:")
    print(f"curl -X POST {BASE_URL}/api/v1/voice \\")
    print("  -H \"Content-Type: application/x-www-form-urlencoded\" \\")
    print("  -d \"CallSid=CA1234567890abcdef&From=%2B1234567890&To=%2B0987654321\"")
    print()
    
    print("2. Test recording endpoint:")
    print(f"curl -X POST {BASE_URL}/api/v1/handle-recording \\")
    print("  -H \"Content-Type: application/x-www-form-urlencoded\" \\")
    print("  -d \"RecordingUrl=https://api.twilio.com/recordings/test.mp3&RecordingSid=RE123&RecordingDuration=15\"")
    print("-" * 50)

if __name__ == "__main__":
    print("Twilio Voice Endpoint Test Client")
    print("=" * 50)
    print("Make sure your Flask server is running before running these tests!")
    print("Start the server by running: python app.py")
    print("=" * 50)
    
    # Run tests
    test_voice_endpoint()
    test_recording_endpoint()
    test_voice_endpoint_with_curl_command()
    
    print("All tests completed!")
