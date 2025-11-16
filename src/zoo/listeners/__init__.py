"""Zoo Listener agents for utterance analysis."""

from .base import BaseListener, ListenerError, ListenerConfigError, ListenerProcessingError
from .filler_falcon import FillerFalcon
from .tempo_tiger import TempoTiger
from .lexi_lynx import LexiLynx

# GrammarGiraffe requires additional dependencies (Ollama client)
# Make it optional for environments without full setup
try:
    from .grammar_giraffe import GrammarGiraffe
    __all__ = [
        'BaseListener',
        'ListenerError',
        'ListenerConfigError',
        'ListenerProcessingError',
        'FillerFalcon',
        'TempoTiger',
        'GrammarGiraffe',
        'LexiLynx',
    ]
except ImportError:
    # GrammarGiraffe unavailable (missing dependencies)
    __all__ = [
        'BaseListener',
        'ListenerError',
        'ListenerConfigError',
        'ListenerProcessingError',
        'FillerFalcon',
        'TempoTiger',
        'LexiLynx',
    ]
