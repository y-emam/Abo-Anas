from flask import Blueprint, jsonify, request, Response
from app.services.twilio_service import twilio_service
from app.services.speech_service import speech_service
from app.services.conversation_service import conversation_service
from app.middleware.request_handler import (
    twilio_middleware, 
    session_middleware, 
    request_logger
)
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the blueprint
api_bp = Blueprint('api', __name__)

@api_bp.route('/', methods=['GET'])
def home():
    """Home route that returns a welcome message"""
    return jsonify({
        "message": "Welcome to the AI Voice Assistant API!",
        "status": "success",
        "description": "Real-time voice conversation using Whisper AI, Gemini AI, and ElevenLabs",
        "features": {
            "speech_to_text": "OpenAI Whisper",
            "ai_conversation": "Google Gemini",
            "text_to_speech": "ElevenLabs (Arabic Syrian)",
            "real_time": "True"
        },
        "endpoints": {
            "/voice": "Initial call endpoint - starts conversation",
            "/voice/process": "Conversation processing endpoint - handles real-time audio"
        }
    })

# @api_bp.route('/voice', methods=['POST'])
# @twilio_middleware.validate_twilio_request
# @request_logger.log_request
# def handle_initial_call():
#     """
#     Handle initial incoming call from Twilio
#     Returns TwiML response to start conversation
#     """
#     try:
#         # Extract Twilio data
#         twilio_data = twilio_middleware.extract_twilio_data(request)
#         phone_number = twilio_data.get('from_number', 'unknown')
#         call_sid = twilio_data.get('call_sid', 'unknown')
        
#         logger.info(f"Initial call from {phone_number}, Call SID: {call_sid}")
        
#         # Initialize or get session
#         session_data = session_middleware.get_session(phone_number)
#         session_data.update({
#             'last_activity': datetime.now(),
#             'call_sid': call_sid,
#             'conversation_count': session_data.get('conversation_count', 0) + 1
#         })
#         session_middleware.update_session(phone_number, session_data)
        
#         # Create welcome TwiML response
#         twiml_response = twilio_service.create_welcome_response(phone_number)
        
#         return Response(twiml_response, mimetype='text/xml')
        
#     except Exception as e:
#         logger.error(f"Error in initial call handler: {str(e)}")
#         error_response = twilio_service.create_error_response()
#         return Response(error_response, mimetype='text/xml')

@api_bp.route('/voice', methods=['POST'])
@twilio_middleware.validate_twilio_request
@request_logger.log_request
def process_conversation():
    """
    Process recorded audio for real-time conversation
    This endpoint handles the conversation flow:
    1. Receive recorded audio from Twilio
    2. Transcribe using Whisper AI
    3. Send to Gemini AI for response
    4. Return TwiML with AI response and continue conversation
    """
    try:
        # Extract Twilio data
        twilio_data = twilio_middleware.extract_twilio_data(request)
        phone_number = twilio_data.get('from_number', 'unknown')
        call_sid = twilio_data.get('call_sid', 'unknown')
        recording_url = request.form.get('RecordingUrl')
        
        logger.info(f"Processing conversation for {phone_number}, Call SID: {call_sid}")
        logger.info(f"Recording URL: {recording_url}")
        
        # Check if user wants to end conversation
        if not recording_url:
            logger.info("No recording URL, ending conversation")
            goodbye_response = twilio_service.create_goodbye_response()
            return Response(goodbye_response, mimetype='text/xml')
        
        # Transcribe audio using Whisper
        logger.info("Transcribing audio with Whisper...")
        user_text = speech_service.transcribe_audio_from_url(recording_url)
        
        if not user_text:
            logger.warning("Failed to transcribe audio")
            error_response = twilio_service.create_error_response("لم أتمكن من فهم ما قلته. يرجى المحاولة مرة أخرى.")
            return Response(error_response, mimetype='text/xml')
        
        logger.info(f"Transcribed text: {user_text}")
        
        # Check if user wants to end conversation
        if twilio_service.detect_conversation_end(user_text):
            logger.info("User requested to end conversation")
            goodbye_response = twilio_service.create_goodbye_response()
            return Response(goodbye_response, mimetype='text/xml')
        
        # Get AI response using Gemini
        logger.info("Getting AI response from Gemini...")
        ai_response = conversation_service.get_conversation_response(
            user_input=user_text,
            phone_number=phone_number,
            language="arabic"
        )
        
        logger.info(f"AI response: {ai_response}")
        
        # Update session data
        session_data = session_middleware.get_session(phone_number)
        session_data.update({
            'last_activity': datetime.now(),
            'last_user_input': user_text,
            'last_ai_response': ai_response
        })
        session_middleware.update_session(phone_number, session_data)
        
        # Create TwiML response with AI answer and continue conversation
        twiml_response = twilio_service.create_conversation_response(
            ai_response=ai_response,
            phone_number=phone_number
        )
        
        return Response(twiml_response, mimetype='text/xml')
        
    except Exception as e:
        logger.error(f"Error in conversation processing: {str(e)}")
        error_response = twilio_service.create_error_response("عذراً، حدث خطأ تقني. يرجى المحاولة مرة أخرى.")
        return Response(error_response, mimetype='text/xml')
