from __future__ import annotations
import io
from pydub import AudioSegment
from openai import OpenAI
from .config import OPENAI_API_KEY

# Initialize OpenAI client once
_client = OpenAI(api_key=OPENAI_API_KEY)


def ogg_bytes_to_wav_bytes(ogg_bytes: bytes) -> bytes:
    """
    Convert Telegram voice message (OGG/Opus) into WAV bytes using pydub + ffmpeg.
    This requires ffmpeg installed globally (check with `ffmpeg -version`).
    """
    audio = AudioSegment.from_file(io.BytesIO(ogg_bytes), format="ogg")
    out = io.BytesIO()
    audio.export(out, format="wav")
    return out.getvalue()


def transcribe_wav_bytes(wav_bytes: bytes) -> str:
    """
    Send WAV audio bytes to OpenAI Whisper API and return the transcription text.
    """
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set in .env")

    buf = io.BytesIO(wav_bytes)
    buf.name = "voice.wav"  # gives a filename hint to OpenAI SDK

    # Call Whisper API
    resp = _client.audio.transcriptions.create(
        model="whisper-1",
        file=buf,
    )
    return (resp.text or "").strip()
