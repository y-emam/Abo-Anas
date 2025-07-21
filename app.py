from flask import Flask, request, jsonify, Response
import json
import os
from dotenv import load_dotenv
from twilio.twiml.voice_response import VoiceResponse

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

@app.route('/api/v1/', methods=['GET'])
def home():
    """Home route that returns a welcome message"""
    return jsonify({
        "message": "Welcome to the Flask Server!",
        "status": "success"
    })

@app.route('/api/v1/data', methods=['POST'])
def handle_post_request():
    """
    Handle POST requests to /api/v1/data
    Accepts JSON data and returns a response
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        
        # Check if data is provided
        if not data:
            return jsonify({
                "error": "No JSON data provided",
                "status": "error"
            }), 400
        
        # Process the data (you can add your logic here)
        response_data = {
            "message": "Data received successfully",
            "received_data": data,
            "status": "success",
            "processed": True
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({
            "error": f"An error occurred: {str(e)}",
            "status": "error"
        }), 500

@app.route('/api/v1/echo', methods=['POST'])
def echo_request():
    """
    Echo endpoint that returns the same data sent to it
    """
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

@app.route('/api/v1/form', methods=['POST'])
def handle_form_data():
    """
    Handle form data POST requests
    """
    try:
        # Get form data
        form_data = request.form.to_dict()
        
        if not form_data:
            return jsonify({
                "error": "No form data provided",
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

@app.route('/api/v1/voice', methods=['POST'])
def handle_voice():
    """
    Handle Twilio voice requests
    Returns TwiML response for voice interactions
    """
    try:
        # Create a TwiML response
        twiml = VoiceResponse()
        
        # Add a greeting message
        twiml.say('Hello! You are connected to the AI assistant.')
        
        # Return TwiML as XML
        response = str(twiml)
        return response, 200, {'Content-Type': 'text/xml'}
        
    except Exception as e:
        # Return error as TwiML
        error_twiml = VoiceResponse()
        error_twiml.say(f'An error occurred: {str(e)}')
        return str(error_twiml), 500, {'Content-Type': 'text/xml'}
    

if __name__ == '__main__':
    # Get configuration from environment variables
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Run the Flask app
    app.run(host=host, port=port, debug=debug)
