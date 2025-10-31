"""Audio module for English Companion NX"""

from .recorder import AudioRecorder
from .player import AudioPlayer
from .wake_word import WakeWordDetector, WakeWordType

__all__ = ['AudioRecorder', 'AudioPlayer', 'WakeWordDetector', 'WakeWordType']