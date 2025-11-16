"""FillerFalcon - Filler word detection listener.

Detects common filler words (um, uh, like, you know, etc.) in user utterances
and emits signals when filler usage exceeds acceptable thresholds.
"""

import re
from typing import List, Optional, Dict, Any
from .base import BaseListener, ListenerProcessingError
from ..signals import Signal, create_filler_signal
from ..zoo_logger import get_zoo_logger


class FillerFalcon(BaseListener):
    """Detects filler words using regex pattern matching.

    Tracks filler usage per utterance and estimates rate over time.
    Emits signals when fillers exceed configured thresholds.

    Configuration:
        filler_patterns: List[str] - Filler words to detect (default: standard set)
        threshold_per_min: float - Max acceptable fillers/min (default: 3.0)
        min_count_for_signal: int - Min fillers in utterance to emit signal (default: 1)
    """

    # Default filler patterns (case-insensitive)
    DEFAULT_FILLERS = [
        r'\buhm\b', r'\buh\b', r'\bum\b', r'\bumm\b',
        r'\blike\b', r'\byou know\b', r'\bbasically\b',
        r'\bactually\b', r'\bkind of\b', r'\bsort of\b',
        r'\bI mean\b', r'\byeah\b', r'\bwell\b',
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize FillerFalcon.

        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config)

        # Get filler patterns from config or use defaults
        patterns = self.get_config_value('filler_patterns', self.DEFAULT_FILLERS)

        # Compile regex patterns for efficient matching
        self.filler_regex = re.compile(
            '|'.join(f'({p})' for p in patterns),
            re.IGNORECASE
        )

        # Get threshold configuration
        self.threshold_per_min = self.get_config_value('threshold_per_min', 3.0)
        self.min_count_for_signal = self.get_config_value('min_count_for_signal', 1)

        # Get logger
        self.logger = get_zoo_logger()

    def process_utterance(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Signal]:
        """Detect filler words in utterance.

        Args:
            text: User's utterance text
            metadata: Optional metadata including:
                - duration_ms: Utterance duration for rate calculation
                - session_history: Recent filler counts for trend analysis
                - utterance_id: Unique identifier

        Returns:
            List of filler signals (may be empty if no fillers detected)
        """
        if not text or not text.strip():
            return []

        try:
            # Find all filler matches with positions
            matches = list(self.filler_regex.finditer(text))

            if not matches:
                return []

            # Extract filler details and filter false positives
            fillers = []
            for match in matches:
                filler_word = match.group(0).lower()
                position = len(text[:match.start()].split())  # Word position

                # Check if this is a false positive (legitimate usage, not filler)
                if self._is_false_positive(text, match, filler_word):
                    continue

                fillers.append({
                    'word': filler_word,
                    'position': position,
                    'char_start': match.start(),
                    'char_end': match.end(),
                })

            total_count = len(fillers)

            # Calculate rate per minute
            rate_per_min = self._calculate_rate(total_count, metadata)

            # Emit signals only if count exceeds minimum threshold
            if total_count < self.min_count_for_signal:
                self.logger.listener_no_signal(self.name)
                return []

            # Create signals for detected fillers
            signals = []

            # Emit one aggregated signal for all fillers in utterance
            # (Could emit per-filler signals, but that's noisy)
            primary_filler = fillers[0]['word']

            signal = create_filler_signal(
                source=self.name,
                filler_word=primary_filler,
                position=fillers[0]['position'],
                total_count=total_count,
                rate_per_min=rate_per_min,
            )

            # Add all filler details to signal data
            signal.data['all_fillers'] = fillers

            signals.append(signal)

            # Log signal emission
            filler_list = ', '.join([f['word'] for f in fillers])
            self.logger.listener_signal(
                self.name,
                signal.type,
                signal.severity,
                f"{total_count}x ({filler_list}) @ {rate_per_min:.1f}/min"
            )

            return signals

        except Exception as e:
            raise ListenerProcessingError(
                f"FillerFalcon failed to process utterance: {e}"
            ) from e

    def _calculate_rate(
        self,
        count: int,
        metadata: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate fillers per minute.

        Args:
            count: Number of fillers in current utterance
            metadata: Optional metadata with duration info

        Returns:
            Estimated fillers per minute
        """
        if not metadata:
            # No timing info - use simple heuristic (assume 2-3s utterance)
            return count * 20  # ~3s utterance → 20 utterances/min

        duration_ms = metadata.get('duration_ms')
        if duration_ms and duration_ms > 0:
            # Calculate exact rate based on utterance duration
            duration_min = duration_ms / 60000.0
            return count / duration_min if duration_min > 0 else 0.0

        # Fallback: estimate based on word count
        word_count = len(metadata.get('text', '').split())
        if word_count > 0:
            # Assume ~150 WPM average speaking rate
            duration_min = word_count / 150.0
            return count / duration_min if duration_min > 0 else 0.0

        # Last resort: simple heuristic
        return count * 20

    def _is_false_positive(
        self,
        text: str,
        match: re.Match,
        filler_word: str
    ) -> bool:
        """Check if detected filler is actually legitimate usage.

        Args:
            text: Full utterance text
            match: Regex match object
            filler_word: The matched filler word

        Returns:
            True if this is a false positive (should be filtered)
        """
        # Special handling for "like" - most common false positive
        if filler_word == "like":
            # Get context around the match
            start_pos = match.start()

            # Check for phrasal verbs: "look like", "seem like", "feel like", "sound like"
            # Get the word before "like"
            text_before = text[:start_pos].strip().lower()
            words_before = text_before.split()

            if words_before:
                prev_word = words_before[-1]
                # Common phrasal verbs with "like"
                if prev_word in ['look', 'looks', 'looked', 'looking',
                                 'seem', 'seems', 'seemed', 'seeming',
                                 'feel', 'feels', 'felt', 'feeling',
                                 'sound', 'sounds', 'sounded', 'sounding',
                                 'taste', 'tastes', 'tasted', 'tasting',
                                 'smell', 'smells', 'smelled', 'smelling']:
                    return True  # This is phrasal verb, not filler

        # "You know" is usually a filler, but "Do you know" is legitimate
        if filler_word == "you know":
            text_before = text[:match.start()].strip().lower()
            if text_before.endswith('do') or text_before.endswith('did'):
                return True  # Question, not filler

        # No false positive detected
        return False
