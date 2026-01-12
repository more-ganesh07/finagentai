import os
import subprocess
import asyncio
import threading
import time
from dotenv import load_dotenv
from speech_to_text import SpeechToText

load_dotenv(override=True)

# ==============================
# CONFIG
# ==============================
DURATION = int(os.getenv("MIC_RECORD_SECONDS", 10))   # default 10 sec max
FFMPEG = os.getenv("FFMPEG_PATH")

# Output file absolute path
OUTPUT_FILE = r"C:\Users\Ganesh.More\Desktop\GaneshMore\KiteInfi\src\stt\mic_ffmpeg.wav"

# Detected microphone device
MIC_DEVICE = "audio=Microphone (Conexant ISST Audio)"


# ==============================
# WAIT FOR ENTER IN ANOTHER THREAD
# ==============================
stop_flag = False

def wait_for_enter():
    global stop_flag
    input("\n🔵 Press ENTER to stop recording early...\n")
    stop_flag = True


# ==============================
# RECORD USING FFMPEG
# ==============================
def record_with_ffmpeg():
    global stop_flag
    stop_flag = False

    # FFmpeg safety check
    if not FFMPEG:
        raise RuntimeError("❌ FFMPEG_PATH missing in .env")

    print("\n========================================")
    print("🎤 VOICE RECORDING MODE")
    print("========================================")
    print("➡ Recording will start when you press ENTER.")
    input("➡ Press ENTER to start recording...")

    print("\n🎙️ Recording started! Speak into your microphone.")
    print("⏳ Max duration:", DURATION, "seconds")
    print("🔵 Press ENTER anytime to stop early.")

    # Start ENTER listener
    listener = threading.Thread(target=wait_for_enter)
    listener.start()

    # Start FFmpeg process
    cmd = [
        FFMPEG,
        "-y",
        "-f", "dshow",
        "-i", MIC_DEVICE,
        "-ac", "1",
        "-ar", "16000",
        OUTPUT_FILE
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    # Timer countdown loop
    for sec in range(DURATION):
        if stop_flag:
            break
        print(f"  ⌛ Recording... {sec+1}/{DURATION} sec", end="\r")
        time.sleep(1)

    # Stop FFmpeg gracefully
    proc.terminate()
    time.sleep(0.5)

    print("\n\n🎧 Recording completed!")
    print(f"📁 Audio saved as: {OUTPUT_FILE}")

    # Print FFmpeg logs if needed
    stderr_output = proc.stderr.read().decode(errors="ignore")
    # print(stderr_output)  # Uncomment for debugging


# ==============================
# TRANSCRIBE USING WHISPER
# ==============================
async def stt_process():
    if not os.path.exists(OUTPUT_FILE):
        raise FileNotFoundError(f"❌ Recording missing: {OUTPUT_FILE}")

    with open(OUTPUT_FILE, "rb") as f:
        audio_bytes = f.read()

    stt = SpeechToText()

    print("\n📝 Transcribing your recording...\n")

    text = await stt.transcribe(audio_bytes)

    print("========================================")
    print("🟢 FINAL TRANSCRIPTION")
    print("========================================")
    print(text)
    print("========================================\n")


# ==============================
# MAIN
# ==============================
if __name__ == "__main__":
    record_with_ffmpeg()
    asyncio.run(stt_process())
