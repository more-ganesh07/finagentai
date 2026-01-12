import assemblyai as aai
from assemblyai.streaming.v3 import (
    BeginEvent,
    StreamingClient,
    StreamingClientOptions,
    StreamingError,
    StreamingEvents,
    StreamingParameters,
    StreamingSessionParameters,
    TerminationEvent,
    TurnEvent,
)
import logging
import pyaudio
from typing import Callable, Optional
from queue import Queue
import threading
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class VoiceToTextService:
    def __init__(self):
        # Load API key from environment
        self.api_key = os.getenv("ASSEMBLY_AI")
        
        if not self.api_key:
            raise ValueError("API key not found. Set ASSEMBLY_AI in .env file")
        
        self.client = None
        self.is_streaming = False
        self.transcript_queue = Queue()
        self.on_transcript_callback = None
        
    def set_transcript_callback(self, callback: Callable[[str], None]):
        """Set callback function to receive transcripts"""
        self.on_transcript_callback = callback
    
    def _on_begin(self, client: StreamingClient, event: BeginEvent):
        logger.info(f"Transcription session started: {event.id}")
        if self.on_transcript_callback:
            self.on_transcript_callback({"status": "started", "session_id": event.id})
    
    def _on_turn(self, client: StreamingClient, event: TurnEvent):
        if event.transcript:
            transcript_data = {
                "text": event.transcript,
                "is_final": event.end_of_turn,
                "is_formatted": event.turn_is_formatted
            }
            self.transcript_queue.put(transcript_data)
            
            if self.on_transcript_callback:
                self.on_transcript_callback(transcript_data)
            
            if event.end_of_turn and not event.turn_is_formatted:
                params = StreamingSessionParameters(format_turns=True)
                client.set_params(params)
    
    def _on_terminated(self, client: StreamingClient, event: TerminationEvent):
        logger.info(f"Session ended: {event.audio_duration_seconds}s processed")
        if self.on_transcript_callback:
            self.on_transcript_callback({
                "status": "terminated",
                "duration": event.audio_duration_seconds
            })
    
    def _on_error(self, client: StreamingClient, error: StreamingError):
        logger.error(f"Streaming error: {error}")
        if self.on_transcript_callback:
            self.on_transcript_callback({"status": "error", "error": str(error)})
    
    def test_microphone(self) -> tuple[bool, str]:
        """Test if microphone is accessible"""
        try:
            p = pyaudio.PyAudio()
            default_input = p.get_default_input_device_info()
            
            test_stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=1024
            )
            test_stream.close()
            p.terminate()
            
            return True, f"Microphone ready: {default_input['name']}"
        except Exception as e:
            return False, f"Microphone error: {str(e)}"
    
    def start_streaming(self, device_index: Optional[int] = None):
        """Start streaming transcription"""
        if self.is_streaming:
            raise RuntimeError("Already streaming")
        
        # Test microphone
        is_available, message = self.test_microphone()
        if not is_available:
            raise RuntimeError(message)
        
        # Create client
        self.client = StreamingClient(
            StreamingClientOptions(
                api_key=self.api_key,
                api_host="streaming.assemblyai.com",
            )
        )
        
        # Register handlers
        self.client.on(StreamingEvents.Begin, self._on_begin)
        self.client.on(StreamingEvents.Turn, self._on_turn)
        self.client.on(StreamingEvents.Termination, self._on_terminated)
        self.client.on(StreamingEvents.Error, self._on_error)
        
        # Connect
        self.client.connect(
            StreamingParameters(
                sample_rate=44100,
                format_turns=True
            )
        )
        
        # Start streaming in thread
        self.is_streaming = True
        stream_thread = threading.Thread(
            target=self._stream_audio,
            args=(device_index,),
            daemon=True
        )
        stream_thread.start()
        
        return "Streaming started"
    
    def _stream_audio(self, device_index: Optional[int] = None):
        """Internal method to stream audio"""
        try:
            mic_params = {"sample_rate": 44100}
            if device_index is not None:
                mic_params["device_index"] = device_index
            
            self.client.stream(aai.extras.MicrophoneStream(**mic_params))
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            self.is_streaming = False
    
    def stop_streaming(self):
        """Stop streaming transcription"""
        if self.client and self.is_streaming:
            self.client.disconnect(terminate=True)
            self.is_streaming = False
            return "Streaming stopped"
        return "Not streaming"
    
    def get_transcript(self, timeout: float = 1.0) -> Optional[dict]:
        """Get next transcript from queue"""
        try:
            return self.transcript_queue.get(timeout=timeout)
        except:
            return None