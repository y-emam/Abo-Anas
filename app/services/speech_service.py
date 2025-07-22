import requests
import tempfile
import os
from app.config import Config
from app.services.google_speech_service import initialize_google_speech_service, get_google_speech_service
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class SpeechService:
    """Service for handling speech-to-text and text-to-speech operations"""
    
    def __init__(self):
        self.elevenlabs_api_key = Config.ELEVENLABS_API_KEY
        
        # Initialize Google Speech service
        try:
            self.google_speech = initialize_google_speech_service(
                credentials_path=Config.GOOGLE_APPLICATION_CREDENTIALS,
                project_id=Config.GOOGLE_PROJECT_ID
            )
            logger.info("Google Speech-to-Text service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Google Speech service: {e}")
            self.google_speech = None
    
    def transcribe_audio_from_url(self, audio_url: str) -> Optional[str]:
        """
        Transcribe audio from URL (Twilio recording)
        Using Google Speech-to-Text API
        
        Args:
            audio_url (str): URL to audio file
            
        Returns:
            Optional[str]: Transcribed text or None if failed
        """
        try:
            if not self.google_speech:
                logger.error("Google Speech service not initialized")
                return None
            
            # Download audio file
            audio_data = self._download_audio(audio_url)
            if not audio_data:
                return None
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            try:
                # Use Google Speech-to-Text API for transcription
                transcription = self._transcribe_with_google_speech(temp_file_path)
                return transcription
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            return None
    
    def _download_audio(self, audio_url: str) -> Optional[bytes]:
        """Download audio file from URL"""
        try:
            response = requests.get(audio_url, timeout=30)
            if response.status_code == 200:
                return response.content
            logger.error(f"Failed to download audio: HTTP {response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Error downloading audio: {str(e)}")
            return None
    
    def _transcribe_with_google_speech(self, audio_file_path: str) -> Optional[str]:
        """
        Transcribe audio using Google Speech-to-Text API
        """
        try:
            if not self.google_speech:
                logger.error("Google Speech service not initialized")
                return None
            
            return self.google_speech.transcribe_audio_file(audio_file_path)
            
        except Exception as e:
            logger.error(f"Error with Google Speech transcription: {str(e)}")
            return None
    
    def detect_speech_end(self, silence_duration: int = 2) -> bool:
        """
        Detect if user has finished speaking based on silence duration
        
        Args:
            silence_duration (int): Seconds of silence to consider speech ended
            
        Returns:
            bool: True if speech has ended
        """
        # This would be implemented with real-time audio analysis
        # For now, return True as placeholder
        return True
    
    def generate_speech_response(self, text: str, gender: str = 'female') -> Tuple[Optional[str], int]:
        """
        Generate speech response using ElevenLabs
        
        Args:
            text (str): Text to convert to speech
            gender (str): Voice gender preference
            
        Returns:
            Tuple[Optional[str], int]: (file_path, status_code)
        """
        from app.services.voice_service import generate_arabic_voice, cleanup_temp_file
        
        try:
            # Generate audio using existing voice service
            audio_generator = generate_arabic_voice(text, gender)
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            
            # Write audio data
            for chunk in audio_generator:
                temp_file.write(chunk)
            
            temp_file.close()
            return temp_file.name, 200
            
        except Exception as e:
            print(f"Error generating speech: {str(e)}")
            return None, 500

    def transcribe_audio_bytes(self, audio_bytes: bytes) -> Optional[str]:
        """
        Transcribe audio bytes directly using Google Speech-to-Text API
        For real-time streaming audio processing
        
        Args:
            audio_bytes (bytes): Raw audio data from Twilio stream
            
        Returns:
            Optional[str]: Transcribed text or None if failed
        """
        try:
            if not self.google_speech:
                logger.error("Google Speech service not initialized")
                return None
            
            # Use Google Speech-to-Text for direct bytes transcription
            return self.google_speech.transcribe_audio_bytes(audio_bytes)
            
        except Exception as e:
            logger.error(f"Error transcribing audio bytes: {str(e)}")
            return None
    
    def create_streaming_session(self, 
                                on_interim_result=None,
                                on_final_result=None,
                                on_error=None):
        """
        Create a new real-time streaming session for continuous transcription
        
        Args:
            on_interim_result: Callback for partial results
            on_final_result: Callback for final results (text, confidence)
            on_error: Callback for errors
            
        Returns:
            StreamingSession object or None if service not available
        """
        try:
            if not self.google_speech:
                logger.error("Google Speech service not initialized")
                return None
            
            return self.google_speech.create_streaming_session(
                on_interim_result=on_interim_result,
                on_final_result=on_final_result,
                on_error=on_error
            )
            
        except Exception as e:
            logger.error(f"Error creating streaming session: {str(e)}")
            return None

# Global instance
speech_service = SpeechService()
