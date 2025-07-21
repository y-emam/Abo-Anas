from elevenlabs.client import ElevenLabs
from app.config import Config
import os
import tempfile

# Initialize ElevenLabs client
client = ElevenLabs(
    api_key=Config.ELEVENLABS_API_KEY
) if Config.ELEVENLABS_API_KEY else None

# Arabic Syrian voice options
ARABIC_VOICES = {
    'male': 'pNInz6obpgDQGcFmaJgB',      # Adam (good for Arabic)
    'female': 'EXAVITQu4vr4xnSDxMaL'     # Bella (good for Arabic)
}

def generate_arabic_voice(text, gender='male', model="eleven_multilingual_v2"):
    """
    Generate Arabic voice audio using ElevenLabs
    
    Args:
        text (str): Text to convert to speech
        gender (str): 'male' or 'female' voice option
        model (str): ElevenLabs model to use
    
    Returns:
        bytes: Audio data
    """
    if not client:
        raise Exception("ElevenLabs API key not configured")
    
    voice_id = ARABIC_VOICES.get(gender, ARABIC_VOICES['female'])
    
    # Use the correct API method according to ElevenLabs documentation
    audio = client.text_to_speech.convert(
        text=text,
        voice_id=voice_id,
        model_id=model,
        output_format="mp3_44100_128"
    )
    
    return audio

def cleanup_temp_file(file_path):
    """
    Clean up temporary audio file
    
    Args:
        file_path (str): Path to temporary file
    """
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
    except Exception:
        pass  # Ignore cleanup errors

def process_voice_request(gender='female', message=None):
    """
    Service to generate Arabic Syrian voice message using ElevenLabs
    
    Args:
        gender (str): 'male' or 'female' voice option
        message (str): Custom message, if None uses default welcome message
    
    Returns:
        tuple: (audio_file_path, status_code, headers)
    """
    try:
        # Default welcoming message in Arabic Syrian
        if message is None:
            welcome_messages = {
                'male': "أهلاً وسهلاً فيك، نورت المكان. كيفك وشو أخبارك؟ أنا هون لمساعدتك بأي شي تحتاجه.",
                'female': "أهلاً حبيبي، أهلاً وسهلاً فيك. كيف الحال وشو الأخبار؟ أنا هون عشان ساعدك بكل شي تريده."
            }
            text_to_speak = welcome_messages.get(gender, welcome_messages['female'])
        else:
            text_to_speak = message
        
        # Generate audio using ElevenLabs
        audio_generator = generate_arabic_voice(text_to_speak, gender)
        
        # Create temporary file to store audio
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        
        # Write audio data to file
        for chunk in audio_generator:
            temp_file.write(chunk)
        
        temp_file.close()
        
        return temp_file.name, 200, {'Content-Type': 'audio/mpeg'}
        
    except Exception as e:
        # Return error message
        error_msg = f"عذراً، حدث خطأ في إنشاء الرسالة الصوتية: {str(e)}"
        return error_msg, 500, {'Content-Type': 'text/plain'}
