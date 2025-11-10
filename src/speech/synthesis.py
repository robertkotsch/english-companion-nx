"""
Speech synthesis module for English Companion NX
Handles text-to-speech using Coqui TTS
"""

import re
import time
from pathlib import Path
from uuid import uuid4

import numpy as np
import soundfile as sf
import torch
from TTS.api import TTS

from src.core.config import Config


def convert_markdown_emphasis_to_pauses(text: str) -> str:
    """
    Convert markdown emphasis (bold/italic) to natural pauses for TTS

    Since VITS doesn't support prosody control, we simulate emphasis by:
    - Bold (**word**) → slight pause before word (comma)
    - Italic (*word*) → keep as-is
    - ALL CAPS → keep as-is (TTS naturally emphasizes)

    Args:
        text: Text with markdown formatting

    Returns:
        Text with emphasis converted to pauses
    """
    # Convert bold+italic to emphasized word with pause
    text = re.sub(r'\*\*\*([^\*]+)\*\*\*', r', \1,', text)
    text = re.sub(r'___([^_]+)___', r', \1,', text)

    # Convert bold to word with slight pause (comma before)
    text = re.sub(r'\*\*([^\*]+)\*\*', r', \1', text)
    text = re.sub(r'__([^_]+)__', r', \1', text)

    # Remove italic markers (keep word unchanged)
    text = re.sub(r'\*([^\*]+)\*', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)

    # Clean up double commas and spaces
    text = re.sub(r',\s*,', ',', text)
    text = re.sub(r'\s+,', ',', text)
    text = re.sub(r',\s+', ', ', text)

    return text


def strip_markdown(text: str, preserve_emphasis: bool = True) -> str:
    """
    Strip markdown formatting from text for TTS

    Removes:
    - Bold (**text** or __text__) - optionally converts to pauses
    - Italic (*text* or _text_) - removes markers
    - Bullet points (* item)
    - Numbered lists (1. item)
    - Headers (# Header)
    - Code blocks (```code```)
    - Inline code (`code`)
    - Links ([text](url))
    - Strikethrough (~~text~~)

    Args:
        text: Text with markdown formatting
        preserve_emphasis: If True, convert bold to pauses; if False, remove completely

    Returns:
        Plain text suitable for TTS
    """
    # Remove code blocks first (multiline)
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)

    # Remove inline code
    text = re.sub(r'`([^`]+)`', r'\1', text)

    # Remove links but keep link text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

    # Handle bold/italic - either preserve as emphasis or remove
    if preserve_emphasis:
        text = convert_markdown_emphasis_to_pauses(text)
    else:
        # Remove bold/italic completely (order matters - do bold first)
        text = re.sub(r'\*\*\*([^\*]+)\*\*\*', r'\1', text)  # Bold+italic
        text = re.sub(r'___([^_]+)___', r'\1', text)
        text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)  # Bold
        text = re.sub(r'__([^_]+)__', r'\1', text)
        text = re.sub(r'\*([^\*]+)\*', r'\1', text)  # Italic
        text = re.sub(r'_([^_]+)_', r'\1', text)

    # Remove strikethrough
    text = re.sub(r'~~([^~]+)~~', r'\1', text)

    # Remove headers (# ## ###)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

    # Remove bullet points at start of lines
    text = re.sub(r'^\s*[\*\-\+]\s+', '', text, flags=re.MULTILINE)

    # Remove numbered lists at start of lines
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)

    # Clean up extra whitespace
    text = re.sub(r'\n\s+', '\n', text)  # Remove leading spaces after newlines
    text = re.sub(r'\n{3,}', '\n\n', text)  # Max 2 newlines in a row
    text = text.strip()

    return text


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
            text: Text to synthesize (markdown will be stripped automatically)

        Returns:
            Path to synthesized audio file
        """
        print("🎙️  Synthesizing speech...")
        start_time = time.time()

        # Strip markdown formatting before TTS
        # Optionally preserve emphasis (bold) as pauses
        clean_text = strip_markdown(text, preserve_emphasis=Config.TTS_PRESERVE_EMPHASIS)

        # Generate temp file path
        temp_file = self.temp_dir / f"tts_{uuid4()}.wav"

        # Synthesize
        self.tts.tts_to_file(text=clean_text, file_path=str(temp_file))

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
