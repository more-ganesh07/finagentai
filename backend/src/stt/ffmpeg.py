import assemblyai as aai

# Replace with your API key
api_key = "75a96a1964d54a369cb8f0c0fa28d521"

def transcribe_audio_file(audio_file_path):
    """Transcribe an audio file"""
    aai.settings.api_key = api_key
    
    transcriber = aai.Transcriber()
    
    print(f"Uploading and transcribing: {audio_file_path}")
    transcript = transcriber.transcribe(audio_file_path)
    
    if transcript.status == aai.TranscriptStatus.error:
        print(f"Error: {transcript.error}")
    else:
        print(f"\nTranscription:\n{transcript.text}")
    
    return transcript.text

# Usage
audio_file = "path/to/your/audio.mp3"  # or .wav, .m4a, etc.
transcribe_audio_file(audio_file)