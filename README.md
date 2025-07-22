# AI Voice Assistant with Real-time Google Speech-to-Text

A real-time conversational AI voice assistant that uses Twilio for phone calls, Google Speech-to-Text for real-time transcription, Google Gemini for intelligent responses, and ElevenLabs for Arabic text-to-speech.

## 🆕 What's New - Real-time Streaming

**This project has been upgraded from OpenAI Whisper to Google Speech-to-Text with real-time streaming capabilities!**

### Before vs After

| Feature | OpenAI Whisper (Old) | Google Speech-to-Text (New) |
|---------|---------------------|---------------------------|
| **Processing** | Batch (wait for complete audio) | Real-time streaming |
| **Latency** | 2-5 seconds | < 1 second |
| **Interim Results** | ❌ No | ✅ Yes (immediate feedback) |
| **Arabic Support** | Good | Excellent with multiple dialects |
| **Real-time** | ❌ No | ✅ True streaming |

### Quick Start - Real-time Version

1. **Set up Google Cloud Speech-to-Text** (see [GOOGLE_SPEECH_SETUP.md](GOOGLE_SPEECH_SETUP.md))
2. **Configure environment**: Copy `.env.example` to `.env` and add your credentials
3. **Test setup**: `python test_google_speech.py`
4. **Start real-time server**: `start_realtime.bat` (Windows) or `start_realtime.sh` (Linux/Mac)

### Legacy Version

If you prefer the original Whisper implementation, use `python app.py` instead.

## Features

- **Real-time Voice Conversations**: Handle incoming phone calls with natural voice interactions
- **🆕 Streaming Transcription**: Immediate partial results as users speak
- **🆕 Low Latency**: < 1 second response time with Google Speech-to-Text
- **Arabic Language Support**: Enhanced support for Arabic (Syrian dialect) conversations
- **AI-Powered Responses**: Uses Google Gemini AI for intelligent conversation responses
- **High-Quality Speech**: ElevenLabs text-to-speech for natural-sounding Arabic voices
- **Session Management**: Maintains conversation context across multiple exchanges
- **Twilio Integration**: Full TwiML support for phone call handling
- **🆕 Real-time WebSocket**: Streaming audio processing with immediate feedback

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Twilio Call   │────│  Flask API      │────│   Gemini AI     │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              │
                       ┌─────────────────┐
                       │   ElevenLabs    │
                       │   (Speech)      │
                       └─────────────────┘
```

## Project Structure

```
abo-anas/
├── app/
│   ├── routes/
│   │   └── api_routes.py          # Main API endpoints
│   ├── services/
│   │   ├── conversation_service.py # Gemini AI integration
│   │   ├── twilio_service.py      # Twilio TwiML handling
│   │   ├── speech_service.py      # Speech processing
│   │   └── voice_service.py       # ElevenLabs integration
│   ├── middleware/
│   │   └── request_handler.py     # Request validation & logging
│   └── config.py                  # Configuration management
├── app.py                         # Flask application entry point
├── requirements.txt               # Python dependencies
├── setup.bat / setup.sh          # Setup scripts
└── README.md                      # This file
```

## Setup Instructions

### 1. Prerequisites

- Python 3.8+
- Twilio Account with phone number
- Google Gemini API key
- ElevenLabs API key
- ngrok (for local development)

### 2. Quick Setup

Run the setup script for your platform:

**Windows:**
```cmd
setup.bat
```

**Linux/Mac:**
```bash
chmod +x setup.sh
./setup.sh
```

### 3. Manual Setup

1. **Create virtual environment:**
```bash
python -m venv myenv
source myenv/bin/activate  # Linux/Mac
# or
myenv\Scripts\activate     # Windows
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables:**
Create a `.env` file with your API keys:
```env
# Flask Configuration
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-here

# ElevenLabs Configuration
ELEVENLABS_API_KEY=your-elevenlabs-api-key

# Gemini AI Configuration
GEMINI_API_KEY=your-gemini-api-key

# Twilio Configuration
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token

# Your Flask app base URL (for Twilio webhooks)
FLASK_BASE_URL=https://your-ngrok-url.ngrok.io
```

### 4. Get API Keys

1. **Gemini AI**: Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. **ElevenLabs**: Sign up at [ElevenLabs](https://elevenlabs.io/) and get your API key
3. **Twilio**: Sign up at [Twilio](https://www.twilio.com/) and get your Account SID and Auth Token

### 5. Run the Application

```bash
python app.py
```

### 6. Expose with ngrok

In a separate terminal:
```bash
ngrok http 5000
```

Copy the ngrok URL and update your `.env` file's `FLASK_BASE_URL`.

### 7. Configure Twilio Webhook

1. Go to your Twilio Console
2. Navigate to Phone Numbers → Manage → Active numbers
3. Click on your phone number
4. Set the webhook URL to: `https://your-ngrok-url.ngrok.io/voice`
5. Set HTTP method to `POST`

## API Endpoints

### Main Endpoints

- `GET /` - Welcome message and API information
- `POST /voice` - Initial call handler (Twilio webhook)
- `POST /voice/process` - Conversation processing (Twilio webhook)
- `POST /voice/status` - Call status updates (Twilio webhook)

### Development/Testing Endpoints

- `GET/POST /voice/test` - Test conversation without phone call
- `POST /voice/clear-session/<phone_number>` - Clear conversation history

### Testing the Conversation

Test the AI conversation without making a phone call:

```bash
curl "http://localhost:5000/voice/test?message=مرحبا&phone=test_user"
```

Response:
```json
{
  "user_input": "مرحبا",
  "ai_response": "أهلاً وسهلاً! كيف بدك أساعدك اليوم؟",
  "status": "success"
}
```

## How It Works

1. **Incoming Call**: User calls your Twilio number
2. **Welcome**: System greets user in Arabic and waits for speech
3. **Speech Recognition**: Twilio converts speech to text
4. **AI Processing**: Gemini AI generates intelligent response
5. **Text-to-Speech**: ElevenLabs converts response to Arabic speech
6. **TwiML Response**: System speaks back to user and waits for next input
7. **Conversation Loop**: Process continues until user says goodbye

## Conversation Flow

```
User calls → Welcome message → User speaks → Speech-to-text → 
Gemini AI → Response → Text-to-speech → User hears response → 
User speaks again... (loop continues)
```

## Voice Options

The system supports both male and female Arabic voices:
- **Female**: Natural Syrian Arabic voice (default)
- **Male**: Natural Syrian Arabic voice

## Session Management

- Each phone number gets its own conversation session
- Conversation history is maintained during the call
- Sessions are cleared when calls end
- Automatic cleanup of old sessions

## Error Handling

The system handles various error scenarios:
- Low confidence speech recognition
- API failures (Gemini, ElevenLabs)
- Network timeouts
- Invalid requests

## Development

### Adding New Features

1. **New Services**: Add to `app/services/`
2. **Middleware**: Add to `app/middleware/`
3. **Routes**: Add to `app/routes/`
4. **Configuration**: Update `app/config.py`

### Testing

Test individual components:

```bash
# Test conversation service
python -c "from app.services.conversation_service import conversation_service; print(conversation_service.get_conversation_response('مرحبا', 'test_user'))"

# Test voice generation
curl "http://localhost:5000/voice/test?message=مرحبا"
```

## Troubleshooting

### Common Issues

1. **"No API key configured"**: Check your `.env` file
2. **ngrok connection issues**: Make sure ngrok is running and URL is updated
3. **Twilio webhook errors**: Check Twilio webhook configuration
4. **Speech recognition fails**: Check Twilio speech settings and language configuration

### Logging

The application logs all important events. Check the console output for:
- Incoming calls
- Speech recognition results
- AI responses
- Errors and warnings

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
   ELEVENLABS_API_KEY=your-elevenlabs-api-key
   ELEVENLABS_VOICE_ID=pNInz6obpgDQGcFmaJgB
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

### 5. Arabic Syrian Voice Generation Endpoint
- **URL:** `GET /voice` or `POST /voice`
- **Description:** Generates Arabic Syrian voice audio using ElevenLabs TTS
- **Content-Type:** Returns `audio/mpeg`
- **Query Parameters:**
  - `gender`: `male` or `female` (default: `female`)
  - `message`: Custom Arabic message (optional, uses default welcome message if not provided)
- **Response:** MP3 audio file

**Examples:**
```bash
# Generate female voice with default welcome message
curl -X GET http://localhost:5000/voice?gender=female -o female_voice.mp3

# Generate male voice with default welcome message
curl -X GET http://localhost:5000/voice?gender=male -o male_voice.mp3

# Generate female voice with custom message
curl -X GET "http://localhost:5000/voice?gender=female&message=مرحبا بك في موقعنا" -o custom_voice.mp3
```

**Voice Configuration:**
- Uses ElevenLabs `eleven_multilingual_v2` model for best Arabic support
- Output format: MP3 (44.1kHz, 128kbps)
- Voices optimized for Arabic Syrian dialect

**Default Welcome Messages:**
- **Male:** "أهلاً وسهلاً فيك، نورت المكان. كيفك وشو أخبارك؟ أنا هون لمساعدتك بأي شي تحتاجه."
- **Female:** "أهلاً حبيبي، أهلاً وسهلاً فيك. كيف الحال وشو الأخبار؟ أنا هون عشان ساعدك بكل شي تريده."

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

### Test Arabic voice generation:
Run the voice generation test:
```bash
python test_voice_generation.py
```

### Test voice API endpoints:
Run the API usage test:
```bash
python test_api_usage.py
```

Make sure the Flask server is running before executing any test clients.

## Project Structure

```
abo-anas/
├── myenv/                      # Virtual environment
├── app/                        # Application package
│   ├── __init__.py
│   ├── config.py              # Configuration settings
│   ├── routes/                # Route blueprints
│   │   ├── __init__.py
│   │   └── api_routes.py      # API route definitions
│   ├── services/              # Business logic services
│   │   ├── __init__.py
│   │   └── voice_service.py   # ElevenLabs voice generation
│   └── logic/                 # Additional logic modules
│       ├── __init__.py
│       ├── data_logic.py
│       └── voice_logic.py
├── app.py                     # Main Flask application
├── test_client.py             # Test client for API endpoints
├── test_voice_generation.py   # Test Arabic voice generation
├── test_api_usage.py          # Test voice API usage
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Dependencies

- Flask: Web framework for Python
- requests: HTTP library for making requests (used in test client)
- python-dotenv: Load environment variables from .env file
- elevenlabs: ElevenLabs SDK for AI-powered text-to-speech

## Features

- Multiple POST endpoints for different data types
- JSON data processing
- Form data handling
- Echo functionality for testing
- **Arabic Syrian Text-to-Speech using ElevenLabs**
- **Male and Female voice options**
- **Custom message support**
- Error handling with proper HTTP status codes
- Debug mode enabled for development
