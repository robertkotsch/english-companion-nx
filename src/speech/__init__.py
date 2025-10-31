"""Speech processing module for English Companion NX"""

from .transcription import TranscriptionService
from .synthesis import SynthesisService

__all__ = ['TranscriptionService', 'SynthesisService']