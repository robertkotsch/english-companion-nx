"""
Speech transcription module for English Companion NX
Handles speech-to-text using Whisper model
"""

import time
import whisper
import torch
from src.core.config import Config


class TranscriptionService:
    """Speech-to-text service using Whisper"""

    def __init__(self, model_size: str = None, device: str = None):
        """
        Initialize transcription service

        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            device: Device to use (cuda or cpu)
        """
        self.model_size = model_size or Config.WHISPER_MODEL
        self.device = device or ("cuda" if torch.cuda.is_available() and Config.USE_GPU else "cpu")

        print(f"   Loading Whisper ({self.model_size}) on {self.device.upper()}...")
        self.model = whisper.load_model(self.model_size, device=self.device)

    def transcribe(self, audio_file: str) -> str:
        """
        Transcribe audio file to text

        Args:
            audio_file: Path to audio file

        Returns:
            Transcribed text
        """
        print("🤖 Transcribing...")
        start_time = time.time()

        result = self.model.transcribe(
            audio_file,
            fp16=(self.device == "cuda")
        )

        transcribe_time = time.time() - start_time
        text = result["text"].strip()

        print(f"✅ Transcribed ({transcribe_time:.2f}s): \"{text}\"")
        return text

    def get_model_info(self) -> dict:
        """Get information about loaded model"""
        return {
            "model_size": self.model_size,
            "device": self.device
        }
