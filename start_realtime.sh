#!/bin/bash

# AI Voice Assistant - Real-time Google Speech-to-Text Version
# This script starts the voice assistant with real-time streaming capabilities

echo "================================"
echo "AI Voice Assistant - Real-time"
echo "Google Speech-to-Text Streaming"  
echo "================================"
echo

# Check if virtual environment exists
if [ ! -f "myenv/bin/activate" ]; then
    echo "ERROR: Virtual environment not found!"
    echo "Please run setup.sh first to create the virtual environment."
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source myenv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "WARNING: .env file not found!"
    echo "Please copy .env.example to .env and configure your API keys."
    echo
    echo "Required configuration:"
    echo "- GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json"
    echo "- GOOGLE_PROJECT_ID=your-google-cloud-project-id"
    echo "- ELEVENLABS_API_KEY=your-elevenlabs-key"
    echo "- GEMINI_API_KEY=your-gemini-key"
    echo "- TWILIO_ACCOUNT_SID=your-twilio-sid"
    echo "- TWILIO_AUTH_TOKEN=your-twilio-token"
    echo
    exit 1
fi

# Test Google Speech setup first
echo
echo "Testing Google Speech-to-Text setup..."
python test_google_speech.py

if [ $? -ne 0 ]; then
    echo
    echo "ERROR: Google Speech test failed!"
    echo "Please check your Google Cloud configuration."
    echo "See GOOGLE_SPEECH_SETUP.md for setup instructions."
    exit 1
fi

# Start the real-time voice assistant
echo
echo "Starting AI Voice Assistant with real-time streaming..."
echo
echo "Features:"
echo "- Real-time Google Speech-to-Text streaming"
echo "- Low-latency audio processing"
echo "- Immediate partial transcription results"
echo "- Enhanced Arabic language support"
echo
echo "Press Ctrl+C to stop the server"
echo

python app_realtime.py

echo
echo "Server stopped."
