import os
import asyncio
import sounddevice as sd
from scipy.io.wavfile import write
from dotenv import load_dotenv
from speech_to_text import SpeechToText

load_dotenv(override=True)


# ==========================================================
# CONFIG FROM .ENV
# ==========================================================
SAMPLERATE = int(os.getenv("MIC_SAMPLE_RATE", 16000))
DURATION = int(os.getenv("MIC_RECORD_SECONDS", 5))
AUDIO_PATH = os.getenv("MIC_OUTPUT_FILE", "mic_record.wav")


# ==========================================================
# RECORD MICROPHONE AUDIO
# ==========================================================
def record_audio():
    print(f"\n🎤 Recording {DURATION} seconds… Speak now!\n")

    recording = sd.rec(
        int(DURATION * SAMPLERATE),
        samplerate=SAMPLERATE,
        channels=1,
        dtype='int16'
    )
    sd.wait()

    write(AUDIO_PATH, SAMPLERATE, recording)

    print(f"🎧 Recording saved as: {AUDIO_PATH}")


# ==========================================================
# USE YOUR EXISTING STT MODULE
# ==========================================================
async def run_stt():
    if not os.path.exists(AUDIO_PATH):
        print("❌ ERROR: Audio file not found.")
        return

    with open(AUDIO_PATH, "rb") as f:
        audio_bytes = f.read()

    stt = SpeechToText()

    print("\n📝 Transcribing audio…\n")

    try:
        text = await stt.transcribe(audio_bytes)
    except Exception as e:
        print(f"❌ STT ERROR: {e}")
        return

    print("\n==============================")
    print("🟢 FINAL TRANSCRIPTION RESULT:")
    print(text)
    print("==============================\n")


# ==========================================================
# MAIN
# ==========================================================
if __name__ == "__main__":
    record_audio()
    asyncio.run(run_stt())
