import requests
import tempfile
import os
import openai
from app.config import Config
from typing import Optional, Tuple

class SpeechService:
    """Service for handling speech-to-text and text-to-speech operations"""
    
    def __init__(self):
        self.elevenlabs_api_key = Config.ELEVENLABS_API_KEY
    
    def transcribe_audio_from_url(self, audio_url: str) -> Optional[str]:
        """
        Transcribe audio from URL (Twilio recording)
        Using OpenAI Whisper API or Google Speech-to-Text
        
        Args:
            audio_url (str): URL to audio file
            
        Returns:
            Optional[str]: Transcribed text or None if failed
        """
        try:
            # Download audio file
            audio_data = self._download_audio(audio_url)
            if not audio_data:
                return None
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            try:
                # Use OpenAI Whisper API for transcription
                transcription = self._transcribe_with_whisper(temp_file_path)
                return transcription
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            print(f"Error transcribing audio: {str(e)}")
            return None
    
    def _download_audio(self, audio_url: str) -> Optional[bytes]:
        """Download audio file from URL"""
        try:
            response = requests.get(audio_url, timeout=30)
            if response.status_code == 200:
                return response.content
            return None
        except Exception as e:
            print(f"Error downloading audio: {str(e)}")
            return None
    
    def _transcribe_with_whisper(self, audio_file_path: str) -> Optional[str]:
        """
        Transcribe audio using OpenAI Whisper API
        """
        try:
            # Initialize OpenAI client
            openai.api_key = Config.OPENAI_API_KEY
            client = openai.OpenAI()
            
            # Open and transcribe the audio file
            with open(audio_file_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="ar"  # Arabic language
                )
                return transcript.text
            
        except Exception as e:
            print(f"Error with Whisper transcription: {str(e)}")
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

# Global instance
speech_service = SpeechService()
