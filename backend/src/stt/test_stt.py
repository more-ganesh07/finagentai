import os
import asyncio
from dotenv import load_dotenv
from speech_to_text import SpeechToText

load_dotenv(override=True)


async def main():
    print("\n[TEST] Starting STT Test...")

    audio_path = os.getenv("STT_TEST_AUDIO")

    if not audio_path:
        print("❌ ERROR: STT_TEST_AUDIO missing in .env")
        return

    if not os.path.exists(audio_path):
        print(f"❌ Audio file not found:\n{audio_path}")
        return

    print(f"[TEST] Using audio: {audio_path}")

    with open(audio_path, "rb") as f:
        audio_bytes = f.read()

    stt = SpeechToText()

    print("[TEST] Running transcription...\n")

    try:
        text = await stt.transcribe(audio_bytes)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return

    print("🟢 ====== TRANSCRIPTION RESULT ======")
    print(text)
    print("🟢 ==================================\n")


if __name__ == "__main__":
    asyncio.run(main())
