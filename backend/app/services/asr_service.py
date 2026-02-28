"""ASR service wrapping OpenAI Whisper batch transcription API."""

import dataclasses
import io
import logging
import wave

import openai

from app.config import settings

logger = logging.getLogger(__name__)

# Minimum audio duration in bytes (0.5s at 16kHz, mono, 16-bit = 16000 bytes)
MIN_AUDIO_BYTES = 16000


@dataclasses.dataclass
class ASRResult:
    transcript: str
    language: str
    confidence: float


def pcm_to_wav(
    pcm_bytes: bytes,
    sample_rate: int = 16000,
    channels: int = 1,
    sample_width: int = 2,
) -> bytes:
    """Wrap raw PCM bytes in a WAV header."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)
    return buf.getvalue()


class ASRService:
    """OpenAI Whisper batch transcription service."""

    def __init__(self):
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        self._client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

    async def transcribe(
        self, audio_bytes: bytes, language: str | None = None
    ) -> ASRResult:
        """Transcribe complete audio using Whisper API.

        Args:
            audio_bytes: WAV audio bytes (16kHz, mono, 16-bit PCM).
            language: Optional ISO-639-1 language hint ("en", "hi", etc.).

        Returns:
            ASRResult with transcript text and detected language.
        """
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "audio.wav"  # OpenAI needs a filename

        kwargs: dict = {
            "model": settings.whisper_model,
            "file": audio_file,
            "response_format": "verbose_json",
        }
        lang = language or settings.whisper_language
        if lang:
            kwargs["language"] = lang

        response = await self._client.audio.transcriptions.create(**kwargs)

        return ASRResult(
            transcript=response.text,
            language=getattr(response, "language", None) or "en",
            confidence=0.95,  # Whisper doesn't return confidence; use high default
        )


# Singleton
_asr_service: ASRService | None = None


def get_asr_service() -> ASRService:
    """Get the singleton ASR service instance."""
    global _asr_service
    if _asr_service is None:
        _asr_service = ASRService()
    return _asr_service
