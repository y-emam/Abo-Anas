#!/bin/bash

# Setup script for AI Voice Assistant

echo "Setting up AI Voice Assistant..."

# Create virtual environment if it doesn't exist
if [ ! -d "myenv" ]; then
    echo "Creating virtual environment..."
    python -m venv myenv
fi

# Activate virtual environment
echo "Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source myenv/Scripts/activate
else
    source myenv/bin/activate
fi

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file template..."
    cat > .env << EOL
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
EOL
    echo "Created .env file. Please fill in your API keys!"
fi

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Fill in your API keys in the .env file"
echo "2. Install ngrok and expose your Flask app"
echo "3. Configure your Twilio phone number webhook to point to your Flask app"
echo "4. Run the app with: python app.py"
