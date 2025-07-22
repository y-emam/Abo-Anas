"""
Real-time AI Voice Assistant with Google Speech-to-Text Streaming
This version uses Google Cloud Speech-to-Text API for real-time transcription
instead of OpenAI Whisper batch processing.
"""

import os
from app import create_app
from app.config import config

def main():
    """Main application entry point with real-time Google Speech support"""
    
    # Check if Google Speech credentials are configured
    google_creds = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    google_project = os.getenv('GOOGLE_PROJECT_ID')
    
    if not google_creds or not google_project:
        print("❌ ERROR: Google Speech-to-Text not configured!")
        print("\nTo use real-time speech recognition, you need to:")
        print("1. Set up Google Cloud project and enable Speech-to-Text API")
        print("2. Create service account and download JSON key")
        print("3. Set these environment variables:")
        print("   GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account.json")
        print("   GOOGLE_PROJECT_ID=your-google-cloud-project-id")
        print("\nSee GOOGLE_SPEECH_SETUP.md for detailed instructions.")
        print("\nFalling back to legacy Whisper mode...")
        use_realtime = False
    else:
        print("✅ Google Speech-to-Text credentials found")
        print(f"   Project ID: {google_project}")
        print(f"   Credentials: {google_creds}")
        use_realtime = True
    
    # Get configuration name from environment
    config_name = os.getenv('FLASK_ENV', 'default')
    
    # Create the Flask app
    if use_realtime:
        # Import the real-time version
        from app.__init___realtime import create_app
        app, socketio = create_app(config_name, use_realtime=True)
    else:
        # Import the legacy version
        from app import create_app
        app, socketio = create_app(config_name)
    
    # Get configuration object
    app_config = config[config_name]
    
    print(f"\n🚀 Starting AI Voice Assistant Server")
    print(f"   Mode: {'Real-time Google Speech' if use_realtime else 'Legacy Whisper'}")
    print(f"   Host: {app_config.FLASK_HOST}")
    print(f"   Port: {app_config.FLASK_PORT}")
    print(f"   Debug: {app_config.FLASK_DEBUG}")
    print(f"   Base URL: {app_config.FLASK_BASE_URL}")
    
    if use_realtime:
        print(f"\n📞 Real-time Voice Endpoints:")
        print(f"   Voice: POST {app_config.FLASK_BASE_URL}/api/v1/voice")
        print(f"   WebSocket: wss://{app_config.FLASK_BASE_URL.replace('https://', '')}/ws")
        print(f"   Health: GET {app_config.FLASK_BASE_URL}/api/v1/health")
        print(f"   Test: POST {app_config.FLASK_BASE_URL}/api/v1/test-transcription")
    
    print(f"\n💡 For help setting up Google Speech-to-Text, see: GOOGLE_SPEECH_SETUP.md")
    print(f"🌐 Make sure to update FLASK_BASE_URL with your ngrok URL for Twilio webhooks")
    print("=" * 70)
    
    # Run the Flask app with SocketIO
    try:
        socketio.run(
            app,
            host=app_config.FLASK_HOST,
            port=app_config.FLASK_PORT,
            debug=app_config.FLASK_DEBUG
        )
    except KeyboardInterrupt:
        print("\n👋 Shutting down AI Voice Assistant...")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")

if __name__ == '__main__':
    main()
