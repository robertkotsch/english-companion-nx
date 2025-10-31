"""
Audio playback module for English Companion NX
Handles playing audio through PulseAudio output device
"""

import subprocess
from src.core.config import Config


class AudioPlayer:
    """Manages audio playback through speakers"""

    def __init__(self):
        """Initialize audio player"""
        self.output_device = Config.AUDIO_OUTPUT_DEVICE

    def play(self, audio_file: str):
        """
        Play audio file through speaker

        Args:
            audio_file: Path to audio file to play

        Raises:
            Exception: If playback fails
        """
        print("🔊 Playing response...")

        result = subprocess.run(
            [
                "paplay",
                f"--device={self.output_device}",
                audio_file
            ],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise Exception(f"Playback failed: {result.stderr}")

        print("✅ Playback complete")
