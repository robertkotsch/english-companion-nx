"""
Configuration management for English Companion NX
Loads settings from .env file and provides typed configuration
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

class Config:
    """Application configuration"""

    # Ollama settings
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "127.0.0.1:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b-instruct")

    # Audio settings
    AUDIO_TEMP_DIR = os.getenv("AUDIO_TEMP_DIR", "/tmp/companion-audio")
    AUDIO_SAMPLE_RATE = int(os.getenv("AUDIO_SAMPLE_RATE", "16000"))
    AUDIO_RECORD_SECONDS = int(os.getenv("AUDIO_RECORD_SECONDS", "5"))

    # Audio device selection (PyAudio for wake word detection)
    # Use device name pattern for robust detection across reboots/USB reconnections
    AUDIO_DEVICE_NAME = os.getenv("AUDIO_DEVICE_NAME", "PowerConf")

    # ALSA input device for Anker PowerConf S3
    AUDIO_INPUT_DEVICE = os.getenv("AUDIO_INPUT_DEVICE", "plughw:0,0")

    # PulseAudio output device for Anker PowerConf S3
    AUDIO_OUTPUT_DEVICE = os.getenv(
        "AUDIO_OUTPUT_DEVICE",
        "alsa_output.usb-Anker_PowerConf_S3_A3321-DEV-SN1-01.analog-stereo"
    )

    # Storage settings
    CONVERSATION_LOG = os.getenv(
        "CONVERSATION_LOG",
        str(Path.home() / "companion-data" / "conversations.jsonl")
    )
    CONVERSATION_BUFFER_INTERVAL = int(os.getenv("CONVERSATION_BUFFER_INTERVAL", "300"))
    CONVERSATION_CONTEXT_SIZE = int(os.getenv("CONVERSATION_CONTEXT_SIZE", "20"))

    # Model settings
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
    TTS_MODEL = os.getenv("TTS_MODEL", "tts_models/en/ljspeech/vits")

    # TTS settings
    TTS_PRESERVE_EMPHASIS = os.getenv("TTS_PRESERVE_EMPHASIS", "true").lower() == "true"

    # Personality settings
    PERSONALITY_PROFILE = os.getenv("PERSONALITY_PROFILE", "casual_friend")

    # Performance settings
    USE_GPU = os.getenv("USE_GPU", "true").lower() == "true"

    # Porcupine Wake Word Detection (Phase 2)
    PORCUPINE_ACCESS_KEY = os.getenv("PORCUPINE_ACCESS_KEY", "")
    PORCUPINE_START_KEYWORD = os.getenv("PORCUPINE_START_KEYWORD", "computer")
    PORCUPINE_STOP_KEYWORD = os.getenv("PORCUPINE_STOP_KEYWORD", "terminator")
    PORCUPINE_START_SENSITIVITY = float(os.getenv("PORCUPINE_START_SENSITIVITY", "0.5"))
    PORCUPINE_STOP_SENSITIVITY = float(os.getenv("PORCUPINE_STOP_SENSITIVITY", "0.5"))

    @classmethod
    def ensure_dirs(cls):
        """Ensure required directories exist"""
        Path(cls.AUDIO_TEMP_DIR).mkdir(parents=True, exist_ok=True)

        # Create conversation log directory if needed
        log_path = Path(cls.CONVERSATION_LOG)
        log_path.parent.mkdir(parents=True, exist_ok=True)

# Initialize directories on import
Config.ensure_dirs()
