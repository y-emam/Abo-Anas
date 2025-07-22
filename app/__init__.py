from flask import Flask
from flask_socketio import SocketIO
from flask_sock import Sock
import os
from app.config import config

def create_app(config_name=None):
    """Application factory pattern"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'default')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize SocketIO and Sock
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
    sock = Sock(app)
    
    # Register blueprints
    from app.routes.api_routes import api_bp, setup_websocket_handlers, setup_websocket_routes
    app.register_blueprint(api_bp, url_prefix='')
    
    # Setup WebSocket handlers
    setup_websocket_handlers(socketio)
    setup_websocket_routes(sock)
    
    return app, socketio
