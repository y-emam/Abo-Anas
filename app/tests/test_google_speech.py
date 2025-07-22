"""
Test script for Google Speech-to-Text real-time streaming
Run this to verify your Google Cloud setup is working correctly.
"""

import os
import time
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_google_speech_setup():
    """Test Google Speech-to-Text configuration"""
    
    print("🧪 Testing Google Speech-to-Text Setup")
    print("=" * 50)
    
    # Check environment variables
    google_creds = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    google_project = os.getenv('GOOGLE_PROJECT_ID')
    
    print(f"📋 Configuration Check:")
    print(f"   GOOGLE_APPLICATION_CREDENTIALS: {'✅ Set' if google_creds else '❌ Missing'}")
    print(f"   GOOGLE_PROJECT_ID: {'✅ Set' if google_project else '❌ Missing'}")
    
    if not google_creds or not google_project:
        print("\n❌ Missing required configuration!")
        print("Please set up Google Cloud credentials first.")
        print("See GOOGLE_SPEECH_SETUP.md for instructions.")
        return False
    
    # Check if credentials file exists
    if not os.path.exists(google_creds):
        print(f"\n❌ Credentials file not found: {google_creds}")
        return False
    
    print(f"   Credentials file: ✅ Found")
    
    # Test Google Speech service initialization
    try:
        print(f"\n🔄 Testing Google Speech service initialization...")
        
        from app.services.google_speech_service import GoogleSpeechService
        
        service = GoogleSpeechService(
            credentials_path=google_creds,
            project_id=google_project
        )
        
        print(f"   Service initialization: ✅ Success")
        
        # Test creating a streaming session
        print(f"\n🔄 Testing streaming session creation...")
        
        results = []
        
        def on_interim(text):
            results.append(f"Interim: {text}")
            print(f"   📝 Interim: {text}")
        
        def on_final(text, confidence):
            results.append(f"Final: {text} (confidence: {confidence:.2f})")
            print(f"   ✅ Final: {text} (confidence: {confidence:.2f})")
        
        def on_error(error):
            results.append(f"Error: {error}")
            print(f"   ❌ Error: {error}")
        
        session = service.create_streaming_session(
            on_interim_result=on_interim,
            on_final_result=on_final,
            on_error=on_error
        )
        
        if session:
            print(f"   Streaming session: ✅ Created successfully")
            
            # Test session lifecycle
            print(f"\n🔄 Testing session lifecycle...")
            session.start()
            print(f"   Session start: ✅ Success")
            
            # Simulate some processing time
            time.sleep(1)
            
            session.stop()
            print(f"   Session stop: ✅ Success")
            
        else:
            print(f"   Streaming session: ❌ Failed to create")
            return False
        
        print(f"\n✅ All tests passed!")
        print(f"🎉 Google Speech-to-Text is ready for real-time streaming!")
        return True
        
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("Please install required dependencies:")
        print("   pip install google-cloud-speech")
        return False
        
    except Exception as e:
        print(f"\n❌ Setup error: {e}")
        print("Please check your Google Cloud configuration.")
        return False

def test_speech_service_integration():
    """Test integration with the main speech service"""
    
    print(f"\n🧪 Testing Speech Service Integration")
    print("=" * 50)
    
    try:
        from app.services.speech_service import speech_service
        
        print(f"🔄 Testing speech service initialization...")
        
        if speech_service.google_speech:
            print(f"   Google Speech integration: ✅ Success")
            
            # Test creating streaming session through speech service
            session = speech_service.create_streaming_session()
            
            if session:
                print(f"   Streaming session via SpeechService: ✅ Success")
                session.start()
                session.stop()
            else:
                print(f"   Streaming session via SpeechService: ❌ Failed")
                return False
                
        else:
            print(f"   Google Speech integration: ❌ Not initialized")
            return False
        
        print(f"\n✅ Speech service integration successful!")
        return True
        
    except Exception as e:
        print(f"\n❌ Integration error: {e}")
        return False

def main():
    """Main test function"""
    
    print("🚀 Google Speech-to-Text Test Suite")
    print("=" * 70)
    
    # Test 1: Basic setup
    setup_ok = test_google_speech_setup()
    
    if not setup_ok:
        print(f"\n❌ Setup test failed. Please fix configuration first.")
        return
    
    # Test 2: Integration
    integration_ok = test_speech_service_integration()
    
    if setup_ok and integration_ok:
        print(f"\n🎉 All tests passed!")
        print(f"✅ Your Google Speech-to-Text setup is working correctly.")
        print(f"🚀 You can now run the real-time voice assistant:")
        print(f"   python app_realtime.py")
    else:
        print(f"\n❌ Some tests failed. Please check the errors above.")

if __name__ == '__main__':
    main()
