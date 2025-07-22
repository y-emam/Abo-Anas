from flask import Flask
from flask_socketio import SocketIO
from flask_sock import Sock
import os
from app.config import config

def create_app(config_name=None, use_realtime=True):
    """Application factory pattern with optional real-time Google Speech support"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'default')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize SocketIO and Sock
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
    sock = Sock(app)
    
    # Choose which routes to use based on configuration
    use_google_speech = os.getenv('USE_GOOGLE_SPEECH', 'true').lower() == 'true'
    
    if use_google_speech and use_realtime:
        # Use new real-time Google Speech routes
        from app.routes.real_time_api_routes import api_bp, setup_websocket_routes
        app.register_blueprint(api_bp, url_prefix='/api/v1')
        
        # Setup WebSocket routes for real-time streaming
        setup_websocket_routes(sock)
        
        print("✅ Using Google Speech-to-Text with Real-time Streaming")
    else:
        # Use original Whisper-based routes
        from app.routes.api_routes import api_bp, setup_websocket_handlers, setup_websocket_routes
        app.register_blueprint(api_bp, url_prefix='')
        
        # Setup WebSocket handlers
        setup_websocket_handlers(socketio)
        setup_websocket_routes(sock)
        
        print("⚠️  Using legacy OpenAI Whisper (batch processing)")
    
    return app, socketio
