from flask import request, session
from functools import wraps
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TwilioMiddleware:
    """Middleware for handling Twilio-specific request processing"""
    
    @staticmethod
    def validate_twilio_request(f):
        """
        Decorator to validate Twilio webhook requests
        In production, you should verify the Twilio signature
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Log incoming request
            logger.info(f"Received Twilio request: {request.method} {request.url}")
            logger.info(f"Form data: {dict(request.form)}")
            
            # Basic validation
            if request.method not in ['POST', 'GET']:
                logger.warning(f"Invalid method: {request.method}")
                return "Method not allowed", 405
            
            # In production, add signature validation here
            # from twilio.request_validator import RequestValidator
            # validator = RequestValidator(Config.TWILIO_AUTH_TOKEN)
            # if not validator.validate(request.url, request.form, request.headers.get('X-Twilio-Signature', '')):
            #     return "Unauthorized", 401
            
            return f(*args, **kwargs)
        return decorated_function
    
    @staticmethod
    def extract_twilio_data(request_obj) -> Dict[str, Any]:
        """
        Extract relevant data from Twilio webhook request
        
        Args:
            request_obj: Flask request object
            
        Returns:
            Dict containing extracted Twilio data
        """
        return {
            'call_sid': request_obj.form.get('CallSid'),
            'account_sid': request_obj.form.get('AccountSid'),
            'from_number': request_obj.form.get('From'),
            'to_number': request_obj.form.get('To'),
            'call_status': request_obj.form.get('CallStatus'),
            'direction': request_obj.form.get('Direction'),
            'speech_result': request_obj.form.get('SpeechResult'),
            'confidence': request_obj.form.get('Confidence'),
            'recording_url': request_obj.form.get('RecordingUrl'),
            'digits': request_obj.form.get('Digits'),
            'caller_city': request_obj.form.get('CallerCity'),
            'caller_state': request_obj.form.get('CallerState'),
            'caller_country': request_obj.form.get('CallerCountry')
        }

class SessionMiddleware:
    """Middleware for managing conversation sessions"""
    
    def __init__(self):
        # In production, use Redis or database for session storage
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    def get_session(self, phone_number: str) -> Dict[str, Any]:
        """
        Get or create session for phone number
        
        Args:
            phone_number (str): User's phone number
            
        Returns:
            Dict containing session data
        """
        if phone_number not in self.sessions:
            self.sessions[phone_number] = {
                'conversation_count': 0,
                'last_activity': None,
                'language_preference': 'arabic',
                'voice_preference': 'female',
                'context': {}
            }
        
        return self.sessions[phone_number]
    
    def update_session(self, phone_number: str, data: Dict[str, Any]):
        """
        Update session data
        
        Args:
            phone_number (str): User's phone number
            data (Dict): Data to update
        """
        if phone_number in self.sessions:
            self.sessions[phone_number].update(data)
        else:
            self.sessions[phone_number] = data
    
    def clear_session(self, phone_number: str):
        """
        Clear session for phone number
        
        Args:
            phone_number (str): User's phone number
        """
        if phone_number in self.sessions:
            del self.sessions[phone_number]
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """
        Clean up old sessions
        
        Args:
            max_age_hours (int): Maximum age of sessions in hours
        """
        from datetime import datetime, timedelta
        
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        expired_sessions = []
        for phone_number, session_data in self.sessions.items():
            last_activity = session_data.get('last_activity')
            if last_activity and last_activity < cutoff_time:
                expired_sessions.append(phone_number)
        
        for phone_number in expired_sessions:
            del self.sessions[phone_number]
        
        logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

class RequestLogger:
    """Middleware for logging requests and responses"""
    
    @staticmethod
    def log_request(f):
        """Decorator to log incoming requests"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            logger.info(f"Request: {request.method} {request.path}")
            logger.info(f"Headers: {dict(request.headers)}")
            logger.info(f"Form data: {dict(request.form)}")
            
            result = f(*args, **kwargs)
            
            logger.info(f"Response status: {getattr(result, 'status_code', 'Unknown')}")
            
            return result
        return decorated_function

# Global instances
session_middleware = SessionMiddleware()
twilio_middleware = TwilioMiddleware()
request_logger = RequestLogger()
