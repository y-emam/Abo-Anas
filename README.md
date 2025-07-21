# Flask Server with POST Requests

A simple Flask server that handles POST requests with multiple endpoints.

## Setup

1. **Activate the virtual environment:**
   ```bash
   myenv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   The `.env` file contains configuration settings. You can modify these as needed:
   ```
   FLASK_ENV=development
   FLASK_DEBUG=True
   FLASK_HOST=0.0.0.0
   FLASK_PORT=5000
   SECRET_KEY=your-secret-key-here
   API_VERSION=v1
   TWILIO_ACCOUNT_SID=your-twilio-account-sid
   TWILIO_AUTH_TOKEN=your-twilio-auth-token
   TWILIO_PHONE_NUMBER=your-twilio-phone-number
   ```

## Running the Server

Start the Flask server:
```bash
python app.py
```

The server will run on `http://localhost:5000`

## API Endpoints

### 1. Home Route
- **URL:** `GET /`
- **Description:** Returns a welcome message
- **Response:** JSON with welcome message

### 2. JSON Data Endpoint
- **URL:** `POST /api/v1/data`
- **Description:** Accepts JSON data and processes it
- **Content-Type:** `application/json`
- **Request Body:** Any valid JSON
- **Response:** JSON with processed data

**Example:**
```bash
curl -X POST http://localhost:5000/api/v1/data \
  -H "Content-Type: application/json" \
  -d '{"name": "John", "age": 30}'
```

### 3. Echo Endpoint
- **URL:** `POST /api/v1/echo`
- **Description:** Returns the same data that was sent to it
- **Content-Type:** `application/json`
- **Request Body:** Any valid JSON
- **Response:** JSON with echoed data

**Example:**
```bash
curl -X POST http://localhost:5000/api/v1/echo \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello World!"}'
```

### 4. Form Data Endpoint
- **URL:** `POST /api/v1/form`
- **Description:** Accepts form data
- **Content-Type:** `application/x-www-form-urlencoded`
- **Request Body:** Form data
- **Response:** JSON with form data

**Example:**
```bash
curl -X POST http://localhost:5000/api/v1/form \
  -d "username=testuser&email=test@example.com"
```

### 5. Twilio Voice Endpoint
- **URL:** `POST /api/v1/voice`
- **Description:** Handles Twilio voice requests and returns TwiML responses
- **Content-Type:** `application/x-www-form-urlencoded`
- **Request Body:** Twilio voice webhook data
- **Response:** TwiML XML for voice instructions

**Example:**
```bash
curl -X POST http://localhost:5000/api/v1/voice \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "CallSid=CA123&From=%2B1234567890&To=%2B0987654321"
```

### 6. Recording Handler Endpoint
- **URL:** `POST /api/v1/handle-recording`
- **Description:** Processes recorded voice data from Twilio
- **Content-Type:** `application/x-www-form-urlencoded`
- **Request Body:** Twilio recording webhook data
- **Response:** TwiML XML response

**Example:**
```bash
curl -X POST http://localhost:5000/api/v1/handle-recording \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "RecordingUrl=https://api.twilio.com/recordings/test.mp3&RecordingSid=RE123"
```

## Testing

### Test all endpoints:
Run the main test client to test JSON and form endpoints:
```bash
python test_client.py
```

### Test Twilio voice endpoints:
Run the Twilio-specific test client:
```bash
python test_twilio.py
```

Make sure the Flask server is running before executing any test clients.

## Project Structure

```
abo-anas/
├── myenv/              # Virtual environment
├── app.py              # Main Flask application
├── test_client.py      # Test client for API endpoints
├── test_twilio.py      # Test client for Twilio voice endpoints
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Dependencies

- Flask: Web framework for Python
- requests: HTTP library for making requests (used in test client)
- python-dotenv: Load environment variables from .env file
- twilio: Twilio SDK for handling voice and SMS requests

## Features

- Multiple POST endpoints for different data types
- JSON data processing
- Form data handling
- Echo functionality for testing
- Error handling with proper HTTP status codes
- Debug mode enabled for development
