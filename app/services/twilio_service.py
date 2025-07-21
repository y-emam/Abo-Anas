from twilio.twiml.voice_response import VoiceResponse, Gather, Say, Record, Play
from twilio.rest import Client
from app.config import Config
from typing import Optional, Dict, Any
import os

class TwilioService:
    """Service for handling Twilio voice interactions and TwiML responses"""
    
    def __init__(self):
        self.account_sid = Config.TWILIO_ACCOUNT_SID
        self.auth_token = Config.TWILIO_AUTH_TOKEN
        self.client = Client(self.account_sid, self.auth_token) if self.account_sid and self.auth_token else None
        
        # Base URL for your Flask app (you'll need to set this)
        self.base_url = os.getenv('FLASK_BASE_URL', 'https://your-ngrok-url.ngrok.io')
    
    def create_welcome_response(self, phone_number: str) -> str:
        """
        Create initial TwiML response for incoming calls
        
        Args:
            phone_number (str): Caller's phone number
            
        Returns:
            str: TwiML XML response
        """
        response = VoiceResponse()
        
        # Welcome message using ElevenLabs-generated Arabic
        response.say(
            "أهلاً وسهلاً! أنا مساعدك الذكي. كيف بدك أساعدك اليوم؟",
            voice='Polly.Zeina',  # Arabic voice
            language='ar'
        )
        
        # Record user's response and process it
        response.record(
            action=f'{self.base_url}/voice/process',
            method='POST',
            max_length=30,  # Maximum 30 seconds per recording
            finish_on_key='#',  # User can press # to finish
            play_beep=False,
            timeout=3,  # Stop recording after 3 seconds of silence
            transcribe=False  # We'll use Whisper instead
        )
        
        return str(response)
        response.say(
            "لم أسمع أي رد. يرجى المحاولة مرة أخرى.",
            voice='Polly.Zeina',
            language='ar'
        )
        response.hangup()
        
        return str(response)
    
    def create_conversation_response(self, ai_response: str, phone_number: str) -> str:
        """
        Create TwiML response for ongoing conversation
        
        Args:
            ai_response (str): AI's response to speak
            phone_number (str): Caller's phone number
            
        Returns:
            str: TwiML XML response
        """
        response = VoiceResponse()
        
        # Speak the AI response
        response.say(
            ai_response,
            voice='Polly.Zeina',
            language='ar'
        )
        
        # Record user's next response
        response.record(
            action=f'{self.base_url}/voice/process',
            method='POST',
            max_length=30,  # Maximum 30 seconds per recording
            finish_on_key='#',  # User can press # to finish
            play_beep=False,
            timeout=3,  # Stop recording after 3 seconds of silence
            transcribe=False  # We'll use Whisper instead
        )
        
        return str(response)
        return str(response)
    
    def create_goodbye_response(self) -> str:
        """
        Create TwiML response for ending conversation
        
        Returns:
            str: TwiML XML response
        """
        response = VoiceResponse()
        response.say(
            "شكراً لك على الاتصال. مع السلامة!",
            voice='Polly.Zeina',
            language='ar'
        )
        response.hangup()
        return str(response)
    
    def create_error_response(self, error_message: str = None) -> str:
        """
        Create TwiML response for errors
        
        Args:
            error_message (str): Custom error message
            
        Returns:
            str: TwiML XML response
        """
        response = VoiceResponse()
        
        message = error_message or "عذراً، حدث خطأ تقني. يرجى المحاولة مرة أخرى لاحقاً."
        
        response.say(
            message,
            voice='Polly.Zeina',
            language='ar'
        )
        response.hangup()
        
        return str(response)
    
    def create_timeout_response(self) -> str:
        """
        Create TwiML response for timeouts
        
        Returns:
            str: TwiML XML response
        """
        response = VoiceResponse()
        response.say(
            "لم أسمع رد منك. شكراً لك على الاتصال. مع السلامة!",
            voice='Polly.Zeina',
            language='ar'
        )
        response.hangup()
        return str(response)
    
    def detect_conversation_end(self, user_input: str) -> bool:
        """
        Detect if user wants to end conversation based on their input
        
        Args:
            user_input (str): User's speech input
            
        Returns:
            bool: True if conversation should end
        """
        end_phrases = [
            'مع السلامة', 'باي', 'شكراً', 'خلاص', 'يعطيك العافية',
            'goodbye', 'bye', 'thank you', 'thanks', 'end call'
        ]
        
        user_input_lower = user_input.lower()
        return any(phrase in user_input_lower for phrase in end_phrases)
    
    def get_call_details(self, call_sid: str) -> Optional[Dict[str, Any]]:
        """
        Get details about a specific call
        
        Args:
            call_sid (str): Twilio call SID
            
        Returns:
            Optional[Dict]: Call details or None if not found
        """
        if not self.client:
            return None
        
        try:
            call = self.client.calls(call_sid).fetch()
            return {
                'sid': call.sid,
                'from': call.from_,
                'to': call.to,
                'status': call.status,
                'duration': call.duration,
                'start_time': call.start_time,
                'end_time': call.end_time
            }
        except Exception as e:
            print(f"Error fetching call details: {str(e)}")
            return None

# Global instance
twilio_service = TwilioService()
