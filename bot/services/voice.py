"""Voice transcription via OpenAI Whisper."""
from openai import OpenAI

from bot.config import OPENAI_API_KEY

_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


def transcribe(audio_path: str) -> str:
    """Transcribe an .ogg/.mp3/.wav file to text."""
    if not _client:
        raise RuntimeError("OPENAI_API_KEY not configured")
    with open(audio_path, "rb") as f:
        result = _client.audio.transcriptions.create(
            model = "whisper-1",
            file  = f,
        )
    return result.text
