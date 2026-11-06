from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    ollama_url: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.2")
    ollama_timeout_seconds: int = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "180"))
    ollama_retries: int = int(os.getenv("OLLAMA_RETRIES", "2"))
    whisper_model: str = os.getenv("WHISPER_MODEL", "base")
    whisper_language: str = os.getenv("WHISPER_LANGUAGE", "es")
    audio_seconds: int = int(os.getenv("AUDIO_SECONDS", "5"))
    audio_sample_rate: int = int(os.getenv("AUDIO_SAMPLE_RATE", "16000"))
