from flask import Blueprint, jsonify, request, Response
from flask_socketio import SocketIO, emit
from flask_sock import Sock
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
import json
import base64
import asyncio
from threading import Thread

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# WebSocket URL configuration
WEBSOCKET_URL = "wss://a0da8bdf9611.ngrok-free.app/ws"

# Create the blueprint
api_bp = Blueprint('api', __name__)

# Store active conversations
active_conversations = {}

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
            "real_time": "WebSocket Streaming"
        },
        "endpoints": {
            "/voice": "Initial call endpoint - starts WebSocket stream",
            "/ws": "WebSocket endpoint for real-time audio streaming (Flask-Sock)"
        },
        "websocket_url": WEBSOCKET_URL,
        "websocket_info": {
            "protocol": "WebSocket (Flask-Sock)",
            "purpose": "Twilio Media Stream connection",
            "events": ["start", "media", "stop"]
        }
    })

@api_bp.route('/voice', methods=['POST'])
@twilio_middleware.validate_twilio_request
@request_logger.log_request
def start_websocket_conversation():
    """
    Handle initial incoming call from Twilio
    Returns TwiML response to connect to WebSocket for real-time conversation
    """
    try:
        # Extract Twilio data
        twilio_data = twilio_middleware.extract_twilio_data(request)
        phone_number = twilio_data.get('from_number', 'unknown')
        call_sid = twilio_data.get('call_sid', 'unknown')
        
        logger.info(f"Starting WebSocket conversation for {phone_number}, Call SID: {call_sid}")
        
        # Initialize or get session
        session_data = session_middleware.get_session(phone_number)
        session_data.update({
            'last_activity': datetime.now(),
            'call_sid': call_sid,
            'conversation_count': session_data.get('conversation_count', 0) + 1,
            'conversation_state': 'websocket_active'
        })
        session_middleware.update_session(phone_number, session_data)
        
        # Store conversation context
        active_conversations[call_sid] = {
            'phone_number': phone_number,
            'session_data': session_data,
            'audio_buffer': b'',
            'processing': False,
            'connected': False
        }
        
        # Create TwiML response that connects to WebSocket
        twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Connect>
    <Stream url="{WEBSOCKET_URL}" />
  </Connect>
</Response>"""
        
        return Response(twiml_response, mimetype='text/xml')
        
    except Exception as e:
        logger.error(f"Error starting WebSocket conversation: {str(e)}")
        error_response = twilio_service.create_error_response("عذراً، حدث خطأ في بدء المحادثة.")
        return Response(error_response, mimetype='text/xml')

# WebSocket setup function for Flask-Sock
def setup_websocket_routes(sock):
    """Setup WebSocket routes using Flask-Sock"""
    
    @sock.route('/ws')
    def websocket(ws):
        """Handle Twilio WebSocket connection"""
        logger.info("Twilio WebSocket connection established")
        
        try:
            while True:
                message = ws.receive()
                if message:
                    try:
                        data = json.loads(message)
                        event_type = data.get('event')
                        
                        logger.info(f"Received Twilio WebSocket event: {event_type}")
                        
                        if event_type == 'start':
                            handle_twilio_stream_start(data, ws)
                        elif event_type == 'media':
                            handle_twilio_media_chunk(data, ws)
                        elif event_type == 'stop':
                            handle_twilio_stream_stop(data, ws)
                            break
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse WebSocket message: {e}")
                    except Exception as e:
                        logger.error(f"Error processing WebSocket message: {e}")
                        
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
        finally:
            logger.info("Twilio WebSocket connection closed")

def handle_twilio_stream_start(data, ws):
    """Handle Twilio stream start via direct WebSocket"""
    try:
        start_data = data.get('start', {})
        call_sid = start_data.get('callSid')
        stream_sid = data.get('streamSid')
        
        logger.info(f"Twilio stream started - Call SID: {call_sid}, Stream SID: {stream_sid}")
        
        if call_sid in active_conversations:
            active_conversations[call_sid]['connected'] = True
            active_conversations[call_sid]['stream_sid'] = stream_sid
            active_conversations[call_sid]['websocket'] = ws
            
            # Add a small delay before sending welcome message to ensure connection is stable
            import time
            def delayed_welcome():
                time.sleep(0.5)  # Wait 500ms for connection to stabilize
                welcome_text = "أهلاً وسهلاً! أنا مساعدك الذكي. كيف يمكنني مساعدتك اليوم؟"
                send_twilio_ai_response(call_sid, welcome_text, stream_sid, ws)
            
            Thread(target=delayed_welcome).start()
            
    except Exception as e:
        logger.error(f"Error handling Twilio stream start: {str(e)}")

def handle_twilio_media_chunk(data, ws):
    """Handle Twilio media chunk via direct WebSocket"""
    try:
        media_payload = data.get('media', {})
        audio_payload = media_payload.get('payload')
        stream_sid = data.get('streamSid')
        
        # Find call_sid from stream_sid
        call_sid = None
        for cid, conv in active_conversations.items():
            if conv.get('stream_sid') == stream_sid:
                call_sid = cid
                break
        
        if call_sid and call_sid in active_conversations and audio_payload:
            try:
                audio_data = base64.b64decode(audio_payload)
                active_conversations[call_sid]['audio_buffer'] += audio_data
                
                buffer_size = len(active_conversations[call_sid]['audio_buffer'])
                # Process audio more frequently (1 second instead of 2)
                if buffer_size > 8000:  # 1 second at 8kHz mono (µ-law is 1 byte per sample)
                    Thread(target=process_twilio_audio_buffer, args=(call_sid, stream_sid, ws)).start()
                    
            except Exception as e:
                logger.error(f"Error processing Twilio audio chunk: {str(e)}")
            
    except Exception as e:
        logger.error(f"Error handling Twilio media chunk: {str(e)}")

def handle_twilio_stream_stop(data, ws):
    """Handle Twilio stream stop via direct WebSocket"""
    try:
        stream_sid = data.get('streamSid')
        logger.info(f"Twilio stream stopped - Stream SID: {stream_sid}")
        
        # Find and clean up conversation
        call_sid_to_remove = None
        for call_sid, conv in active_conversations.items():
            if conv.get('stream_sid') == stream_sid:
                call_sid_to_remove = call_sid
                break
        
        if call_sid_to_remove:
            logger.info(f"Cleaning up Twilio conversation for call: {call_sid_to_remove}")
            del active_conversations[call_sid_to_remove]
            
    except Exception as e:
        logger.error(f"Error handling Twilio stream stop: {str(e)}")

def process_twilio_audio_buffer(call_sid, stream_sid, ws):
    """Process audio buffer for Twilio WebSocket"""
    if active_conversations[call_sid]['processing']:
        return
    
    active_conversations[call_sid]['processing'] = True
    
    try:
        conversation = active_conversations[call_sid]
        audio_buffer = conversation['audio_buffer']
        phone_number = conversation['phone_number']
        
        conversation['audio_buffer'] = b''
        
        logger.info(f"Processing Twilio audio buffer for {phone_number}")
        
        user_text = speech_service.transcribe_audio_bytes(audio_buffer)
        
        if user_text and user_text.strip():
            logger.info(f"Transcribed: {user_text}")
            
            if twilio_service.detect_conversation_end(user_text):
                goodbye_text = "شكراً لك! إلى اللقاء."
                send_twilio_ai_response(call_sid, goodbye_text, stream_sid, ws)
                return
            
            ai_response = conversation_service.get_conversation_response(
                user_input=user_text,
                phone_number=phone_number,
                language="arabic"
            )
            
            logger.info(f"AI response: {ai_response}")
            send_twilio_ai_response(call_sid, ai_response, stream_sid, ws)
            
            # Update session data
            session_data = session_middleware.get_session(phone_number)
            session_data.update({
                'last_activity': datetime.now(),
                'last_user_input': user_text,
                'last_ai_response': ai_response
            })
            session_middleware.update_session(phone_number, session_data)
            
    except Exception as e:
        logger.error(f"Error processing Twilio audio buffer: {str(e)}")
    finally:
        if call_sid in active_conversations:
            active_conversations[call_sid]['processing'] = False

def send_twilio_ai_response(call_sid, text_response, stream_sid, ws):
    """Send AI response via Twilio WebSocket"""
    try:
        logger.info(f"Generating Twilio speech for: {text_response}")
        
        from app.services.voice_service import generate_arabic_voice
        
        # Generate audio chunks in µ-law format
        audio_chunks = generate_arabic_voice(text_response, gender='female')
        
        # Send audio chunks to Twilio WebSocket
        for chunk in audio_chunks:
            if len(chunk) > 0:  # Only send non-empty chunks
                audio_base64 = base64.b64encode(chunk).decode('utf-8')
                
                media_message = {
                    "event": "media",
                    "streamSid": stream_sid,
                    "media": {
                        "payload": audio_base64
                    }
                }
                
                ws.send(json.dumps(media_message))
        
        logger.info("Twilio AI response audio sent successfully")
        
    except Exception as e:
        logger.error(f"Error sending Twilio AI response: {str(e)}")
        # Send a fallback message
        try:
            fallback_text = "عذراً، حدث خطأ في الاستجابة الصوتية."
            simple_audio = fallback_text.encode('utf-8')  # Simple fallback
            audio_base64 = base64.b64encode(simple_audio).decode('utf-8')
            
            media_message = {
                "event": "media", 
                "streamSid": stream_sid,
                "media": {
                    "payload": audio_base64
                }
            }
            ws.send(json.dumps(media_message))
        except:
            logger.error("Failed to send fallback message")

# WebSocket event handlers for real-time audio streaming
def setup_websocket_handlers(socketio):
    """Setup WebSocket handlers for real-time conversation"""
    
    @socketio.on('connect')
    def handle_connect():
        logger.info("WebSocket connected for voice streaming")
        emit('connected', {'status': 'Connected to voice stream'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        logger.info("WebSocket disconnected for voice streaming")
    
    @socketio.on('message')
    def handle_media_stream(data):
        """Handle incoming audio stream from Twilio"""
        try:
            logger.info(f"Received WebSocket message: {type(data)}")
            
            # Parse incoming message (could be JSON string or dict)
            if isinstance(data, str):
                try:
                    media_data = json.loads(data)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON: {data}")
                    return
            else:
                media_data = data
            
            event_type = media_data.get('event')
            logger.info(f"WebSocket event: {event_type}")
            
            if event_type == 'start':
                handle_stream_start(media_data)
            elif event_type == 'media':
                handle_media_chunk(media_data)
            elif event_type == 'stop':
                handle_stream_stop(media_data)
            else:
                logger.warning(f"Unknown event type: {event_type}")
                    
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {str(e)}")

def handle_stream_start(data):
    """Handle stream start event"""
    try:
        start_data = data.get('start', {})
        call_sid = start_data.get('callSid')
        stream_sid = data.get('streamSid')
        
        logger.info(f"Media stream started - Call SID: {call_sid}, Stream SID: {stream_sid}")
        
        if call_sid in active_conversations:
            active_conversations[call_sid]['connected'] = True
            active_conversations[call_sid]['stream_sid'] = stream_sid
            
            # Send welcome message with delay
            phone_number = active_conversations[call_sid]['phone_number']
            welcome_text = "أهلاً وسهلاً! أنا مساعدك الذكي. كيف يمكنني مساعدتك اليوم؟"
            
            # Add delay to ensure connection is stable
            import time
            def delayed_welcome():
                time.sleep(0.5)  # Wait 500ms for connection to stabilize
                send_ai_response(call_sid, welcome_text, stream_sid)
            
            Thread(target=delayed_welcome).start()
            
    except Exception as e:
        logger.error(f"Error handling stream start: {str(e)}")

def handle_media_chunk(data):
    """Handle incoming media chunk"""
    try:
        media_payload = data.get('media', {})
        audio_payload = media_payload.get('payload')
        stream_sid = data.get('streamSid')
        
        # Find call_sid from stream_sid
        call_sid = None
        for cid, conv in active_conversations.items():
            if conv.get('stream_sid') == stream_sid:
                call_sid = cid
                break
        
        if call_sid and call_sid in active_conversations and audio_payload:
            # Decode audio data
            try:
                audio_data = base64.b64decode(audio_payload)
                
                # Add to buffer
                active_conversations[call_sid]['audio_buffer'] += audio_data
                
                # Process when we have enough audio (1 second instead of 2)
                buffer_size = len(active_conversations[call_sid]['audio_buffer'])
                if buffer_size > 8000:  # 1 second at 8kHz mono (µ-law is 1 byte per sample)
                    logger.info(f"Processing audio buffer of size: {buffer_size}")
                    Thread(target=process_audio_buffer, args=(call_sid, stream_sid)).start()
                    
            except Exception as e:
                logger.error(f"Error processing audio chunk: {str(e)}")
            
    except Exception as e:
        logger.error(f"Error handling media chunk: {str(e)}")

def handle_stream_stop(data):
    """Handle stream stop event"""
    try:
        stream_sid = data.get('streamSid')
        logger.info(f"Media stream stopped - Stream SID: {stream_sid}")
        
        # Find and clean up conversation
        call_sid_to_remove = None
        for call_sid, conv in active_conversations.items():
            if conv.get('stream_sid') == stream_sid:
                call_sid_to_remove = call_sid
                break
        
        if call_sid_to_remove:
            logger.info(f"Cleaning up conversation for call: {call_sid_to_remove}")
            del active_conversations[call_sid_to_remove]
            
    except Exception as e:
        logger.error(f"Error handling stream stop: {str(e)}")

def process_audio_buffer(call_sid, stream_sid):
    """Process accumulated audio buffer"""
    if active_conversations[call_sid]['processing']:
        return  # Already processing
    
    active_conversations[call_sid]['processing'] = True
    
    try:
        conversation = active_conversations[call_sid]
        audio_buffer = conversation['audio_buffer']
        phone_number = conversation['phone_number']
        
        # Clear buffer
        conversation['audio_buffer'] = b''
        
        logger.info(f"Processing audio buffer for {phone_number}")
        
        # Transcribe audio using Whisper
        user_text = speech_service.transcribe_audio_bytes(audio_buffer)
        
        if user_text and user_text.strip():
            logger.info(f"Transcribed: {user_text}")
            
            # Check if user wants to end conversation
            if twilio_service.detect_conversation_end(user_text):
                goodbye_text = "شكراً لك! إلى اللقاء."
                send_ai_response(call_sid, goodbye_text, stream_sid)
                return
            
            # Get AI response using Gemini
            ai_response = conversation_service.get_conversation_response(
                user_input=user_text,
                phone_number=phone_number,
                language="arabic"
            )
            
            logger.info(f"AI response: {ai_response}")
            
            # Send AI response as audio
            send_ai_response(call_sid, ai_response, stream_sid)
            
            # Update session data
            session_data = session_middleware.get_session(phone_number)
            session_data.update({
                'last_activity': datetime.now(),
                'last_user_input': user_text,
                'last_ai_response': ai_response
            })
            session_middleware.update_session(phone_number, session_data)
        else:
            logger.info("No valid transcription received")
            
    except Exception as e:
        logger.error(f"Error processing audio buffer: {str(e)}")
    finally:
        if call_sid in active_conversations:
            active_conversations[call_sid]['processing'] = False

def send_ai_response(call_sid, text_response, stream_sid):
    """Convert text to speech and send back to Twilio"""
    try:
        logger.info(f"Generating speech for: {text_response}")
        
        # Generate audio using ElevenLabs
        from app.services.voice_service import generate_arabic_voice
        
        # Generate audio chunks in µ-law format
        audio_chunks = generate_arabic_voice(text_response, gender='female')
        
        # Send audio chunks via SocketIO
        from flask_socketio import emit
        
        for chunk in audio_chunks:
            if len(chunk) > 0:  # Only send non-empty chunks
                audio_base64 = base64.b64encode(chunk).decode('utf-8')
                
                # Create media message for Twilio
                media_message = {
                    "event": "media",
                    "streamSid": stream_sid,
                    "media": {
                        "payload": audio_base64
                    }
                }
                
                emit('message', json.dumps(media_message))
        
        logger.info("AI response audio sent successfully")
        
    except Exception as e:
        logger.error(f"Error sending AI response: {str(e)}")
        # Send fallback message
        try:
            from flask_socketio import emit
            fallback_msg = {
                "event": "error",
                "message": "عذراً، حدث خطأ في الاستجابة الصوتية."
            }
            emit('message', json.dumps(fallback_msg))
        except:
            logger.error("Failed to send fallback message")
