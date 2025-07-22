import asyncio
import queue
import threading
import time
from typing import Optional, Generator, Callable
from google.cloud import speech
from google.api_core import exceptions as google_exceptions
import io
import logging

logger = logging.getLogger(__name__)

class GoogleSpeechService:
    """Real-time Google Speech-to-Text service with streaming capabilities"""
    
    def __init__(self, credentials_path: Optional[str] = None, project_id: Optional[str] = None):
        """
        Initialize Google Speech-to-Text client
        
        Args:
            credentials_path: Path to Google Cloud service account JSON file
            project_id: Google Cloud project ID
        """
        try:
            if credentials_path:
                import os
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
            
            self.client = speech.SpeechClient()
            self.project_id = project_id
            
            # Streaming configuration
            self.config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=8000,  # Twilio's default sample rate
                language_code="ar-SA",  # Arabic (Saudi Arabia) - best for Syrian dialect
                alternative_language_codes=["ar", "en-US"],  # Fallback languages
                enable_automatic_punctuation=True,
                enable_word_confidence=True,
                enable_word_time_offsets=True,
                audio_channel_count=1,
                enable_separate_recognition_per_channel=False,
                model="latest_long",  # Best for longer audio segments
                use_enhanced=True,  # Enhanced models for better accuracy
            )
            
            self.streaming_config = speech.StreamingRecognitionConfig(
                config=self.config,
                interim_results=True,  # Get partial results while speaking
                single_utterance=False,  # Continue listening after silence
            )
            
            logger.info("Google Speech-to-Text service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Speech service: {e}")
            raise
    
    def transcribe_audio_file(self, audio_file_path: str) -> Optional[str]:
        """
        Transcribe audio from a file (for backward compatibility)
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            Transcribed text or None if failed
        """
        try:
            with io.open(audio_file_path, "rb") as audio_file:
                content = audio_file.read()
            
            audio = speech.RecognitionAudio(content=content)
            
            response = self.client.recognize(config=self.config, audio=audio)
            
            if response.results:
                # Get the most confident result
                result = response.results[0]
                if result.alternatives:
                    return result.alternatives[0].transcript.strip()
            
            return None
            
        except google_exceptions.GoogleAPIError as e:
            logger.error(f"Google API error during transcription: {e}")
            return None
        except Exception as e:
            logger.error(f"Error transcribing audio file: {e}")
            return None
    
    def transcribe_audio_bytes(self, audio_bytes: bytes) -> Optional[str]:
        """
        Transcribe audio from raw bytes
        
        Args:
            audio_bytes: Raw audio data
            
        Returns:
            Transcribed text or None if failed
        """
        try:
            audio = speech.RecognitionAudio(content=audio_bytes)
            
            response = self.client.recognize(config=self.config, audio=audio)
            
            if response.results:
                result = response.results[0]
                if result.alternatives:
                    confidence = result.alternatives[0].confidence
                    text = result.alternatives[0].transcript.strip()
                    
                    logger.info(f"Transcription confidence: {confidence:.2f}")
                    return text
            
            return None
            
        except google_exceptions.GoogleAPIError as e:
            logger.error(f"Google API error during transcription: {e}")
            return None
        except Exception as e:
            logger.error(f"Error transcribing audio bytes: {e}")
            return None
    
    def create_streaming_session(self, 
                                on_interim_result: Optional[Callable[[str], None]] = None,
                                on_final_result: Optional[Callable[[str, float], None]] = None,
                                on_error: Optional[Callable[[Exception], None]] = None) -> 'StreamingSession':
        """
        Create a new streaming recognition session
        
        Args:
            on_interim_result: Callback for partial results
            on_final_result: Callback for final results (text, confidence)
            on_error: Callback for errors
            
        Returns:
            StreamingSession object
        """
        return StreamingSession(
            self.client,
            self.streaming_config,
            on_interim_result,
            on_final_result,
            on_error
        )


class StreamingSession:
    """Handles a single streaming recognition session"""
    
    def __init__(self, 
                 client: speech.SpeechClient,
                 streaming_config: speech.StreamingRecognitionConfig,
                 on_interim_result: Optional[Callable[[str], None]] = None,
                 on_final_result: Optional[Callable[[str, float], None]] = None,
                 on_error: Optional[Callable[[Exception], None]] = None):
        
        self.client = client
        self.streaming_config = streaming_config
        self.on_interim_result = on_interim_result
        self.on_final_result = on_final_result
        self.on_error = on_error
        
        self.audio_queue = queue.Queue()
        self.closed = False
        self.session_timeout = 300  # 5 minutes timeout
        self.last_audio_time = time.time()
        
        # Threading
        self.recognition_thread = None
        self.session_active = False
    
    def start(self):
        """Start the streaming session"""
        if self.session_active:
            return
        
        self.session_active = True
        self.closed = False
        self.last_audio_time = time.time()
        
        # Start recognition in separate thread
        self.recognition_thread = threading.Thread(target=self._recognition_loop)
        self.recognition_thread.daemon = True
        self.recognition_thread.start()
        
        logger.info("Streaming recognition session started")
    
    def add_audio_data(self, audio_data: bytes):
        """
        Add audio data to the streaming session
        
        Args:
            audio_data: Raw audio bytes
        """
        if not self.session_active or self.closed:
            return
        
        self.last_audio_time = time.time()
        
        try:
            self.audio_queue.put(audio_data, timeout=1.0)
        except queue.Full:
            logger.warning("Audio queue is full, dropping audio data")
    
    def stop(self):
        """Stop the streaming session"""
        self.session_active = False
        self.closed = True
        
        # Signal end of audio stream
        self.audio_queue.put(None)
        
        # Wait for recognition thread to finish
        if self.recognition_thread and self.recognition_thread.is_alive():
            self.recognition_thread.join(timeout=5.0)
        
        logger.info("Streaming recognition session stopped")
    
    def _audio_generator(self):
        """Generator that yields audio data from the queue"""
        while not self.closed:
            try:
                # Check for session timeout
                if time.time() - self.last_audio_time > self.session_timeout:
                    logger.info("Session timeout reached")
                    break
                
                chunk = self.audio_queue.get(timeout=1.0)
                if chunk is None:  # End of stream signal
                    break
                
                yield speech.StreamingRecognizeRequest(audio_content=chunk)
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in audio generator: {e}")
                break
    
    def _recognition_loop(self):
        """Main recognition loop running in separate thread"""
        try:
            # Create the initial request with config
            requests = [speech.StreamingRecognizeRequest(
                streaming_config=self.streaming_config
            )]
            
            # Add audio data requests
            requests.extend(self._audio_generator())
            
            # Start streaming recognition
            responses = self.client.streaming_recognize(requests)
            
            # Process responses
            for response in responses:
                if self.closed:
                    break
                
                if response.error.code != 0:
                    error_msg = f"Speech recognition error: {response.error.message}"
                    logger.error(error_msg)
                    if self.on_error:
                        self.on_error(Exception(error_msg))
                    continue
                
                for result in response.results:
                    if not result.alternatives:
                        continue
                    
                    transcript = result.alternatives[0].transcript
                    confidence = result.alternatives[0].confidence
                    
                    if result.is_final:
                        # Final result
                        if self.on_final_result:
                            self.on_final_result(transcript.strip(), confidence)
                        logger.info(f"Final: '{transcript.strip()}' (confidence: {confidence:.2f})")
                    else:
                        # Interim result
                        if self.on_interim_result:
                            self.on_interim_result(transcript.strip())
                        logger.debug(f"Interim: '{transcript.strip()}'")
        
        except google_exceptions.GoogleAPIError as e:
            error_msg = f"Google API error in recognition loop: {e}"
            logger.error(error_msg)
            if self.on_error:
                self.on_error(e)
        
        except Exception as e:
            error_msg = f"Unexpected error in recognition loop: {e}"
            logger.error(error_msg)
            if self.on_error:
                self.on_error(e)
        
        finally:
            self.session_active = False
            logger.info("Recognition loop ended")


# Global instance
google_speech_service = None

def initialize_google_speech_service(credentials_path: Optional[str] = None, 
                                   project_id: Optional[str] = None) -> GoogleSpeechService:
    """
    Initialize the global Google Speech service instance
    
    Args:
        credentials_path: Path to Google Cloud service account JSON
        project_id: Google Cloud project ID
        
    Returns:
        GoogleSpeechService instance
    """
    global google_speech_service
    
    if google_speech_service is None:
        google_speech_service = GoogleSpeechService(credentials_path, project_id)
    
    return google_speech_service

def get_google_speech_service() -> Optional[GoogleSpeechService]:
    """Get the global Google Speech service instance"""
    return google_speech_service
