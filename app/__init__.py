from flask import Flask
import os
from app.config import config

def create_app(config_name=None):
    """Application factory pattern"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'default')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Register blueprints
    from app.routes.api_routes import api_bp
    app.register_blueprint(api_bp, url_prefix='')
    
    return app
