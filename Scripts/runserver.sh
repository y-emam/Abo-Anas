#!/bin/bash

# Load environment variables from .env file
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "Warning: .env file not found"
fi

# Check if required variables are set
if [ -z "$NGROK_AUTHTOKEN" ]; then
    echo "Error: NGROK_AUTHTOKEN not found in .env file"
    exit 1
fi

if [ -z "$FLASK_PORT" ]; then
    FLASK_PORT=5000
    echo "Using default Flask port: $FLASK_PORT"
fi

# Authenticate ngrok
echo "Authenticating ngrok..."
ngrok config add-authtoken $NGROK_AUTHTOKEN

# Function to cleanup processes on script exit
cleanup() {
    echo "Cleaning up processes..."
    if [ ! -z "$FLASK_PID" ]; then
        kill $FLASK_PID 2>/dev/null
    fi
    if [ ! -z "$NGROK_PID" ]; then
        kill $NGROK_PID 2>/dev/null
    fi
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup INT TERM EXIT

# Start Flask server in background
echo "Starting Flask server on port $FLASK_PORT..."
python app.py &
FLASK_PID=$!

# Wait a moment for Flask to start
sleep 3

# Check if Flask is running
if ! kill -0 $FLASK_PID 2>/dev/null; then
    echo "Error: Flask server failed to start"
    exit 1
fi

echo "Flask server started (PID: $FLASK_PID)"

# Start ngrok tunnel
echo "Starting ngrok tunnel..."
ngrok http $FLASK_PORT &
NGROK_PID=$!

echo "Ngrok tunnel started (PID: $NGROK_PID)"
echo ""
echo "Your Flask app should now be accessible via ngrok!"
echo "Check the ngrok web interface at: http://127.0.0.1:4040"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for user to stop the script
wait