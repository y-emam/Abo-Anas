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

# Store active conversations with streaming sessions
active_conversations = {}
streaming_sessions = {}

@api_bp.route('/', methods=['GET'])
def home():
    """Home route that returns a welcome message"""
    return jsonify({
        "message": "Welcome to the AI Voice Assistant API!",
        "status": "success",
        "description": "Real-time voice conversation using Google Speech-to-Text, Gemini AI, and ElevenLabs",
        "features": {
            "speech_to_text": "Google Speech-to-Text (Real-time Streaming)",
            "ai_conversation": "Google Gemini",
            "text_to_speech": "ElevenLabs (Arabic Syrian)",
            "real_time": "WebSocket Streaming with Live Transcription"
        },
        "endpoints": {
            "/voice": "Initial call endpoint - starts WebSocket stream",
            "/ws": "WebSocket endpoint for real-time audio streaming (Flask-Sock)"
        },
        "websocket_url": WEBSOCKET_URL,
        "websocket_info": {
            "protocol": "Twilio Media Streaming",
            "audio_format": "µ-law encoded audio",
            "sample_rate": "8000Hz",
            "transcription": "Real-time Google Speech-to-Text"
        }
    })

@api_bp.route('/data', methods=['POST'])
def handle_post_request():
    """Handle generic POST requests with JSON data"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "No JSON data received",
                "status": "error"
            }), 400
            
        return jsonify({
            "message": "Data received successfully",
            "received_data": data,
            "status": "success"
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": f"Request processing failed: {str(e)}",
            "status": "error"
        }), 500

@api_bp.route('/echo', methods=['POST'])
def echo_request():
    """Echo endpoint that returns the same data sent to it"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "No data to echo",
                "status": "error"
            }), 400
            
        return jsonify({
            "echo": data,
            "status": "success"
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": f"Echo failed: {str(e)}",
            "status": "error"
        }), 500

@api_bp.route('/form', methods=['POST'])
def handle_form_data():
    """Handle form data POST requests"""
    try:
        form_data = request.form.to_dict()
        
        if not form_data:
            return jsonify({
                "error": "No form data received",
                "status": "error"
            }), 400
            
        return jsonify({
            "message": "Form data received successfully",
            "form_data": form_data,
            "status": "success"
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": f"Form processing failed: {str(e)}",
            "status": "error"
        }), 500

@api_bp.route('/voice', methods=['POST'])
@twilio_middleware
@session_middleware
@request_logger
def handle_voice():
    """Handle Twilio voice requests and initiate real-time streaming"""
    try:
        call_sid = request.form.get('CallSid')
        from_number = request.form.get('From')
        to_number = request.form.get('To')
        
        logger.info(f"Voice call initiated - From: {from_number}, To: {to_number}, Call SID: {call_sid}")
        
        # Initialize conversation state
        active_conversations[call_sid] = {
            'phone_number': from_number,
            'call_sid': call_sid,
            'audio_buffer': b'',
            'processing': False,
            'connected': False,
            'stream_sid': None,
            'websocket': None,
            'conversation_started': datetime.now()
        }
        
        # Create streaming session for real-time transcription
        def on_interim_result(text):
            logger.debug(f"Interim transcription: {text}")
            # Optionally handle partial results for better UX
        
        def on_final_result(text, confidence):
            logger.info(f"Final transcription: '{text}' (confidence: {confidence:.2f})")
            if call_sid in active_conversations:
                # Process the final transcription
                Thread(target=process_transcription_result, args=(call_sid, text)).start()
        
        def on_error(error):
            logger.error(f"Streaming transcription error: {error}")
        
        # Create streaming session
        streaming_session = speech_service.create_streaming_session(
            on_interim_result=on_interim_result,
            on_final_result=on_final_result,
            on_error=on_error
        )
        
        if streaming_session:
            streaming_sessions[call_sid] = streaming_session
            streaming_session.start()
            logger.info(f"Started streaming session for call {call_sid}")
        
        # Generate TwiML to start media streaming
        twiml_response = twilio_service.create_stream_response(
            websocket_url=WEBSOCKET_URL
        )
        
        return Response(twiml_response, mimetype='text/xml')
        
    except Exception as e:
        logger.error(f"Error starting WebSocket conversation: {str(e)}")
        error_response = twilio_service.create_error_response("عذراً، حدث خطأ في بدء المحادثة.")
        return Response(error_response, mimetype='text/xml')

def process_transcription_result(call_sid, user_text):
    """Process the final transcription result"""
    try:
        if call_sid not in active_conversations:
            return
        
        conversation = active_conversations[call_sid]
        phone_number = conversation['phone_number']
        stream_sid = conversation.get('stream_sid')
        ws = conversation.get('websocket')
        
        if not user_text or not user_text.strip():
            return
        
        logger.info(f"Processing transcription for {phone_number}: {user_text}")
        
        # Check for conversation end
        if twilio_service.detect_conversation_end(user_text):
            goodbye_text = "شكراً لك! إلى اللقاء."
            send_twilio_ai_response(call_sid, goodbye_text, stream_sid, ws)
            cleanup_conversation(call_sid)
            return
        
        # Get AI response
        ai_response = conversation_service.get_conversation_response(
            user_input=user_text,
            phone_number=phone_number,
            language="arabic"
        )
        
        logger.info(f"AI response: {ai_response}")
        
        # Send AI response
        if stream_sid and ws:
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
        logger.error(f"Error processing transcription result: {str(e)}")

def cleanup_conversation(call_sid):
    """Clean up conversation and streaming session"""
    try:
        # Stop streaming session
        if call_sid in streaming_sessions:
            streaming_sessions[call_sid].stop()
            del streaming_sessions[call_sid]
            logger.info(f"Stopped streaming session for call {call_sid}")
        
        # Remove conversation
        if call_sid in active_conversations:
            del active_conversations[call_sid]
            logger.info(f"Cleaned up conversation for call {call_sid}")
            
    except Exception as e:
        logger.error(f"Error cleaning up conversation {call_sid}: {str(e)}")

# WebSocket setup function for Flask-Sock
def setup_websocket_routes(sock):
    """Setup WebSocket routes using Flask-Sock"""
    
    @sock.route('/ws')
    def websocket(ws):
        """Handle Twilio WebSocket connection with real-time transcription"""
        logger.info("Twilio WebSocket connection established")
        
        try:
            while True:
                message = ws.receive()
                if message:
                    try:
                        data = json.loads(message)
                        event_type = data.get('event')
                        
                        logger.debug(f"Received Twilio WebSocket event: {event_type}")
                        
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
            
            # Send welcome message after a short delay
            def delayed_welcome():
                import time
                time.sleep(0.5)  # Wait 500ms for connection to stabilize
                welcome_text = "أهلاً وسهلاً! أنا مساعدك الذكي. كيف يمكنني مساعدتك اليوم؟"
                send_twilio_ai_response(call_sid, welcome_text, stream_sid, ws)
            
            Thread(target=delayed_welcome).start()
            
    except Exception as e:
        logger.error(f"Error handling Twilio stream start: {str(e)}")

def handle_twilio_media_chunk(data, ws):
    """Handle Twilio media chunk with real-time streaming transcription"""
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
                # Decode µ-law audio data
                audio_data = base64.b64decode(audio_payload)
                
                # Convert µ-law to PCM for Google Speech
                # µ-law is 8-bit, need to convert to 16-bit PCM
                import audioop
                pcm_data = audioop.ulaw2lin(audio_data, 2)  # Convert to 16-bit PCM
                
                # Send to streaming session
                if call_sid in streaming_sessions:
                    streaming_sessions[call_sid].add_audio_data(pcm_data)
                    
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
            cleanup_conversation(call_sid_to_remove)
            
    except Exception as e:
        logger.error(f"Error handling Twilio stream stop: {str(e)}")

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
            fallback_message = {
                "event": "media",
                "streamSid": stream_sid,
                "media": {
                    "payload": ""  # Empty payload to indicate end
                }
            }
            ws.send(json.dumps(fallback_message))
        except:
            pass

# Additional route for testing real-time transcription
@api_bp.route('/test-transcription', methods=['POST'])
def test_real_time_transcription():
    """Test endpoint for real-time transcription"""
    try:
        # Check if audio file is uploaded
        if 'audio' not in request.files:
            return jsonify({
                "error": "No audio file provided",
                "status": "error"
            }), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({
                "error": "No audio file selected",
                "status": "error"
            }), 400
        
        # Read audio data
        audio_data = audio_file.read()
        
        # Create a test streaming session
        results = []
        
        def on_interim(text):
            results.append({"type": "interim", "text": text})
        
        def on_final(text, confidence):
            results.append({"type": "final", "text": text, "confidence": confidence})
        
        def on_error(error):
            results.append({"type": "error", "message": str(error)})
        
        # Test with streaming session
        session = speech_service.create_streaming_session(
            on_interim_result=on_interim,
            on_final_result=on_final,
            on_error=on_error
        )
        
        if session:
            session.start()
            session.add_audio_data(audio_data)
            session.stop()
            
            return jsonify({
                "message": "Real-time transcription test completed",
                "results": results,
                "status": "success"
            })
        else:
            return jsonify({
                "error": "Failed to create streaming session",
                "status": "error"
            }), 500
            
    except Exception as e:
        logger.error(f"Error in test transcription: {str(e)}")
        return jsonify({
            "error": f"Test failed: {str(e)}",
            "status": "error"
        }), 500

# Health check endpoint
@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Check if Google Speech service is available
        google_speech_available = speech_service.google_speech is not None
        
        return jsonify({
            "status": "healthy",
            "services": {
                "google_speech": google_speech_available,
                "twilio": True,
                "conversation": True
            },
            "active_conversations": len(active_conversations),
            "streaming_sessions": len(streaming_sessions),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500
