import os
from app import create_app
from app.config import config

if __name__ == '__main__':
    # Get configuration name from environment
    config_name = os.getenv('FLASK_ENV', 'default')
    
    # Create the Flask app and SocketIO using the factory pattern
    app, socketio = create_app(config_name)
    
    # Get configuration object
    app_config = config[config_name]
    
    # Run the Flask app with SocketIO
    socketio.run(
        app,
        host=app_config.FLASK_HOST,
        port=app_config.FLASK_PORT,
        debug=app_config.FLASK_DEBUG
    )
