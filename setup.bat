@echo off

echo Setting up AI Voice Assistant...

REM Create virtual environment if it doesn't exist
if not exist "myenv" (
    echo Creating virtual environment...
    python -m venv myenv
)

REM Activate virtual environment
echo Activating virtual environment...
call myenv\Scripts\activate.bat

REM Install requirements
echo Installing requirements...
pip install -r requirements.txt

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo Creating .env file template...
    (
        echo # Flask Configuration
        echo FLASK_HOST=0.0.0.0
        echo FLASK_PORT=5000
        echo FLASK_DEBUG=True
        echo SECRET_KEY=your-secret-key-here
        echo.
        echo # ElevenLabs Configuration
        echo ELEVENLABS_API_KEY=your-elevenlabs-api-key
        echo.
        echo # Gemini AI Configuration
        echo GEMINI_API_KEY=your-gemini-api-key
        echo.
        echo # Twilio Configuration
        echo TWILIO_ACCOUNT_SID=your-twilio-account-sid
        echo TWILIO_AUTH_TOKEN=your-twilio-auth-token
        echo.
        echo # Your Flask app base URL ^(for Twilio webhooks^)
        echo FLASK_BASE_URL=https://your-ngrok-url.ngrok.io
    ) > .env
    echo Created .env file. Please fill in your API keys!
)

echo Setup complete!
echo.
echo Next steps:
echo 1. Fill in your API keys in the .env file
echo 2. Install ngrok and expose your Flask app
echo 3. Configure your Twilio phone number webhook to point to your Flask app
echo 4. Run the app with: python app.py

pause
