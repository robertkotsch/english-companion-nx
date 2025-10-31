"""
Speech synthesis module for English Companion NX
Handles text-to-speech using Coqui TTS
"""

import time
from pathlib import Path
from uuid import uuid4

import numpy as np
import soundfile as sf
import torch
from TTS.api import TTS

from src.core.config import Config


class SynthesisService:
    """Text-to-speech service using Coqui TTS"""

    def __init__(self, model_name: str = None, device: str = None):
        """
        Initialize synthesis service

        Args:
            model_name: TTS model name
            device: Device to use (cuda or cpu)
        """
        self.model_name = model_name or Config.TTS_MODEL
        self.device = device or ("cuda" if torch.cuda.is_available() and Config.USE_GPU else "cpu")
        self.temp_dir = Path(Config.AUDIO_TEMP_DIR)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        print(f"   Loading TTS ({self.model_name}) on {self.device.upper()}...")
        self.tts = TTS(model_name=self.model_name, progress_bar=False).to(self.device)

    def synthesize(self, text: str) -> str:
        """
        Synthesize speech from text

        Args:
            text: Text to synthesize

        Returns:
            Path to synthesized audio file
        """
        print("🎙️  Synthesizing speech...")
        start_time = time.time()

        # Generate temp file path
        temp_file = self.temp_dir / f"tts_{uuid4()}.wav"

        # Synthesize
        self.tts.tts_to_file(text=text, file_path=str(temp_file))

        # Add silence padding to prevent clipping
        audio_data, sample_rate = sf.read(str(temp_file))

        # Add 0.5 seconds of silence at the beginning
        silence_duration = 0.5
        silence_samples = int(silence_duration * sample_rate)

        # Handle mono/stereo
        if len(audio_data.shape) == 1:
            audio_data = audio_data.reshape(-1, 1)

        silence = np.zeros((silence_samples, audio_data.shape[1]))
        padded_audio = np.vstack([silence, audio_data])

        # Save padded audio
        sf.write(str(temp_file), padded_audio, sample_rate)

        synth_time = time.time() - start_time
        print(f"✅ Speech synthesized ({synth_time:.2f}s)")

        return str(temp_file)

    def cleanup_file(self, file_path: str):
        """Delete temporary audio file"""
        try:
            Path(file_path).unlink(missing_ok=True)
        except Exception:
            pass

    def get_model_info(self) -> dict:
        """Get information about loaded model"""
        return {
            "model_name": self.model_name,
            "device": self.device
        }
