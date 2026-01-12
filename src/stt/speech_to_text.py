import os
import tempfile
import asyncio
import subprocess
import mimetypes
import uuid
from typing import AsyncGenerator, Tuple
from dotenv import load_dotenv
from faster_whisper import WhisperModel

load_dotenv(override=True)
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")


# -------------------------------------------------------
# Resolve ffmpeg binary
# -------------------------------------------------------
def get_ffmpeg_binary():
    ffmpeg_path = os.getenv("FFMPEG_PATH")
    if ffmpeg_path and os.path.exists(ffmpeg_path):
        return ffmpeg_path
    return "ffmpeg"  # fallback to system PATH


# -------------------------------------------------------
# Convert any audio → wav 16k mono
# -------------------------------------------------------
def ffmpeg_to_wav(input_path: str, output_path: str, sample_rate=16000):
    ffmpeg_bin = get_ffmpeg_binary()

    cmd = [
        ffmpeg_bin,
        "-y",
        "-i", input_path,
        "-ac", "1",
        "-ar", str(sample_rate),
        "-vn",
        output_path,
    ]

    proc = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    if proc.returncode != 0:
        err = proc.stderr.decode(errors="ignore")
        raise RuntimeError(f"[FFMPEG ERROR] {err}")


# -------------------------------------------------------
# Speech To Text Class
# -------------------------------------------------------
class SpeechToText:
    def __init__(self):
        self.model_name = os.getenv("WHISPER_MODEL", "small")
        self.device = os.getenv("WHISPER_DEVICE", "cpu")

        compute_type = "int8" if self.device == "cpu" else None

        print(f"[STT] Loading Whisper model: {self.model_name} on {self.device}")

        self.model = WhisperModel(
            model_size_or_path=self.model_name,
            device=self.device,
            compute_type=compute_type
        )


    # Save audio to temp file
    def _save_temp(self, audio_bytes, ext=".tmp"):
        path = os.path.join(tempfile.gettempdir(), f"stt_{uuid.uuid4().hex}{ext}")
        with open(path, "wb") as f:
            f.write(audio_bytes)
        return path


    # Convert to wav file
    def _prepare_wav(self, audio_bytes):
        raw_path = self._save_temp(audio_bytes, ".tmp")
        wav_path = raw_path + ".wav"

        ffmpeg_to_wav(raw_path, wav_path)

        os.remove(raw_path)
        return wav_path


    # ---------------------------------------------------
    # Non-streaming transcription
    # ---------------------------------------------------
    async def transcribe(self, audio_bytes: bytes) -> str:
        wav_path = self._prepare_wav(audio_bytes)

        try:
            loop = asyncio.get_running_loop()
            segments, _ = await loop.run_in_executor(
                None,
                lambda: self.model.transcribe(wav_path)
            )

            text = " ".join([s.text for s in segments]).strip()
            return text
        finally:
            if os.path.exists(wav_path):
                os.remove(wav_path)
