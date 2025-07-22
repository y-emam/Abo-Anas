from elevenlabs.client import ElevenLabs
from app.config import Config
import os
import tempfile
import io
import audioop
import wave
import struct
from pydub import AudioSegment
import logging

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
    Generate Arabic voice audio using ElevenLabs and convert for Twilio
    
    Args:
        text (str): Text to convert to speech
        gender (str): 'male' or 'female' voice option
        model (str): ElevenLabs model to use
    
    Returns:
        generator: Audio chunks in µ-law format for Twilio
    """
    logger = logging.getLogger(__name__)
    
    if not client:
        raise Exception("ElevenLabs API key not configured")
    
    voice_id = ARABIC_VOICES.get(gender, ARABIC_VOICES['female'])
    
    try:
        logger.info(f"Generating voice for text: '{text[:50]}...' using voice {voice_id}")
        
        # Try PCM format first (doesn't require ffmpeg), fallback to MP3
        try:
            # Generate audio from ElevenLabs in PCM format
            audio_generator = client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id=model,
                output_format="pcm_22050"  # PCM format, easier to process
            )
            
            # Collect all audio data
            audio_data = b''
            chunk_count = 0
            for chunk in audio_generator:
                audio_data += chunk
                chunk_count += 1
            
            logger.info(f"Received {len(audio_data)} bytes of PCM audio data in {chunk_count} chunks from ElevenLabs")
            
            if len(audio_data) == 0:
                raise Exception("No audio data received from ElevenLabs")
            
            # Convert PCM to proper format for Twilio
            converted_chunks = list(convert_pcm_for_twilio(audio_data, 22050))
            logger.info(f"Converted to {len(converted_chunks)} µ-law chunks for Twilio")
            
            # Return as generator
            for chunk in converted_chunks:
                yield chunk
                
        except Exception as e:
            logger.warning(f"PCM format failed, trying MP3: {e}")
            
            # Fallback to MP3 format
            audio_generator = client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id=model,
                output_format="mp3_22050_32"
            )
            
            # Collect all audio data
            audio_data = b''
            for chunk in audio_generator:
                audio_data += chunk
            
            logger.info(f"Received {len(audio_data)} bytes of MP3 audio data from ElevenLabs")
            
            # Convert to proper format for Twilio
            converted_chunks = list(convert_audio_for_twilio(audio_data))
            logger.info(f"Converted to {len(converted_chunks)} µ-law chunks for Twilio")
            
            # Return as generator
            for chunk in converted_chunks:
                yield chunk
        
    except Exception as e:
        logger.error(f"Error generating voice: {str(e)}")
        
        # Create fallback silence
        logger.info("Generating fallback silence due to error")
        silence_duration_samples = 8000  # 1 second at 8kHz
        mulaw_silence = bytes([0xFF] * silence_duration_samples)
        
        # Split silence into chunks
        chunk_size = 160
        for i in range(0, len(mulaw_silence), chunk_size):
            chunk = mulaw_silence[i:i + chunk_size]
            if len(chunk) > 0:
                yield chunk

def convert_pcm_for_twilio(pcm_data, sample_rate):
    """
    Convert PCM audio data to Twilio-compatible format (8kHz, µ-law)
    
    Args:
        pcm_data (bytes): Raw PCM audio data from ElevenLabs
        sample_rate (int): Original sample rate of the PCM data
    
    Returns:
        generator: Audio chunks in µ-law format for Twilio
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Create AudioSegment from raw PCM data
        # ElevenLabs PCM is typically 16-bit, mono
        audio = AudioSegment(
            data=pcm_data,
            sample_width=2,  # 16-bit = 2 bytes per sample
            frame_rate=sample_rate,
            channels=1  # mono
        )
        
        # Convert to 8kHz sample rate for Twilio
        audio = audio.set_frame_rate(8000)
        
        # Get raw PCM data at 8kHz
        pcm_8k = audio.raw_data
        
        # Convert PCM to µ-law (what Twilio expects)
        mulaw_data = audioop.lin2ulaw(pcm_8k, 2)  # 2 = 16-bit samples
        
        # Split into chunks for streaming
        chunk_size = 160  # 20ms at 8kHz µ-law
        
        for i in range(0, len(mulaw_data), chunk_size):
            chunk = mulaw_data[i:i + chunk_size]
            if len(chunk) > 0:
                yield chunk
                
    except Exception as e:
        logger.error(f"Error converting PCM for Twilio: {str(e)}")
        
        # Create fallback silence
        silence_duration_samples = 8000  # 1 second at 8kHz
        mulaw_silence = bytes([0xFF] * silence_duration_samples)
        
        chunk_size = 160
        for i in range(0, len(mulaw_silence), chunk_size):
            chunk = mulaw_silence[i:i + chunk_size]
            if len(chunk) > 0:
                yield chunk

def convert_audio_for_twilio(audio_data):
    """
    Convert audio data to Twilio-compatible format (8kHz, µ-law)
    
    Args:
        audio_data (bytes): Raw audio data from ElevenLabs (MP3 format)
    
    Returns:
        generator: Audio chunks in µ-law format for Twilio
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Load the MP3 audio using pydub
        audio = AudioSegment.from_mp3(io.BytesIO(audio_data))
        
        # Convert to the format Twilio expects:
        # - Mono (1 channel)
        # - 8kHz sample rate
        # - 16-bit PCM first, then convert to µ-law
        audio = audio.set_channels(1)  # Convert to mono
        audio = audio.set_frame_rate(8000)  # Convert to 8kHz
        audio = audio.set_sample_width(2)  # 16-bit (2 bytes per sample)
        
        # Get raw PCM data
        pcm_data = audio.raw_data
        
        # Convert PCM to µ-law (what Twilio expects)
        mulaw_data = audioop.lin2ulaw(pcm_data, 2)  # 2 = 16-bit samples
        
        # Split into chunks for streaming
        # 160 bytes = 20ms of audio at 8kHz µ-law (8000 samples/sec * 0.02 sec = 160 samples)
        chunk_size = 160
        
        for i in range(0, len(mulaw_data), chunk_size):
            chunk = mulaw_data[i:i + chunk_size]
            if len(chunk) > 0:  # Only yield non-empty chunks
                yield chunk
                
    except Exception as e:
        logger.error(f"Error converting audio for Twilio: {str(e)}")
        
        # Create a simple fallback: 1 second of silence in µ-law format
        # µ-law silence is represented by 0xFF (255 in decimal)
        silence_duration_samples = 8000  # 1 second at 8kHz
        mulaw_silence = bytes([0xFF] * silence_duration_samples)
        
        # Split silence into chunks
        chunk_size = 160
        for i in range(0, len(mulaw_silence), chunk_size):
            chunk = mulaw_silence[i:i + chunk_size]
            if len(chunk) > 0:
                yield chunk

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
