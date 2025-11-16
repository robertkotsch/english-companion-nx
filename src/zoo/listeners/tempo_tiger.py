"""TempoTiger - Speaking tempo and pacing analysis listener.

Analyzes speaking rate (words per minute) and pause patterns in user utterances.
Emits signals for tempo issues like speaking too fast, too slow, or long pauses.
"""

from typing import List, Optional, Dict, Any
from .base import BaseListener, ListenerProcessingError
from ..signals import Signal, create_tempo_signal


class TempoTiger(BaseListener):
    """Analyzes speaking tempo and pacing patterns.

    Uses word timestamps (if available) or duration-based estimation
    to calculate WPM and detect pauses.

    Configuration:
        min_wpm: float - Minimum acceptable WPM (default: 100)
        max_wpm: float - Maximum acceptable WPM (default: 180)
        long_pause_threshold_sec: float - Pause duration to flag (default: 2.0)
        severity_scale: float - Multiplier for severity calculation (default: 1.0)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize TempoTiger.

        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config)

        # WPM thresholds
        self.min_wpm = self.get_config_value('min_wpm', 100)
        self.max_wpm = self.get_config_value('max_wpm', 180)

        # Pause detection
        self.long_pause_threshold = self.get_config_value(
            'long_pause_threshold_sec', 2.0
        )

        # Severity scaling
        self.severity_scale = self.get_config_value('severity_scale', 1.0)

    def process_utterance(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Signal]:
        """Analyze speaking tempo and pacing.

        Args:
            text: User's utterance text
            metadata: Optional metadata including:
                - duration_ms: Total utterance duration
                - word_timestamps: List of word timing info (if available)
                - utterance_id: Unique identifier

        Returns:
            List of tempo-related signals
        """
        if not text or not text.strip():
            return []

        if not metadata:
            # Can't analyze tempo without timing information
            return []

        try:
            signals = []
            word_count = len(text.split())

            # Try to get detailed timing info
            word_timestamps = metadata.get('word_timestamps')
            duration_ms = metadata.get('duration_ms')

            if word_timestamps:
                # Use precise word-level timestamps
                tempo_signals = self._analyze_word_timestamps(
                    word_timestamps, word_count
                )
                signals.extend(tempo_signals)
            elif duration_ms:
                # Fall back to duration-based WPM estimation
                tempo_signals = self._analyze_duration(
                    text, word_count, duration_ms
                )
                signals.extend(tempo_signals)

            return signals

        except Exception as e:
            raise ListenerProcessingError(
                f"TempoTiger failed to process utterance: {e}"
            ) from e

    def _analyze_word_timestamps(
        self,
        word_timestamps: List[Dict[str, Any]],
        word_count: int
    ) -> List[Signal]:
        """Analyze tempo using word-level timestamps.

        Args:
            word_timestamps: List of dicts with 'word', 'start', 'end' keys
            word_count: Total word count

        Returns:
            List of signals for tempo issues
        """
        signals = []

        if not word_timestamps or len(word_timestamps) < 2:
            return signals

        # Calculate overall WPM
        first_start = word_timestamps[0].get('start', 0)
        last_end = word_timestamps[-1].get('end', 0)
        duration_sec = last_end - first_start

        if duration_sec > 0:
            wpm = (word_count / duration_sec) * 60
            wpm_signals = self._check_wpm(wpm)
            signals.extend(wpm_signals)

        # Detect long pauses between words
        pause_signals = self._detect_pauses(word_timestamps)
        signals.extend(pause_signals)

        return signals

    def _analyze_duration(
        self,
        text: str,
        word_count: int,
        duration_ms: int
    ) -> List[Signal]:
        """Analyze tempo using only total duration.

        Args:
            text: Utterance text
            word_count: Number of words
            duration_ms: Total duration in milliseconds

        Returns:
            List of signals for tempo issues
        """
        signals = []

        duration_min = duration_ms / 60000.0
        if duration_min > 0 and word_count > 0:
            wpm = word_count / duration_min
            wpm_signals = self._check_wpm(wpm)
            signals.extend(wpm_signals)

        return signals

    def _check_wpm(self, wpm: float) -> List[Signal]:
        """Check if WPM is within acceptable range.

        Args:
            wpm: Calculated words per minute

        Returns:
            List of signals (empty if WPM is acceptable)
        """
        signals = []

        if wpm < self.min_wpm:
            # Too slow
            deviation = (self.min_wpm - wpm) / self.min_wpm
            severity = min(1.0, deviation * self.severity_scale)

            signal = create_tempo_signal(
                source=self.name,
                issue_type="too_slow",
                wpm=wpm,
                severity=severity,
                target_wpm=self.min_wpm,
            )
            signals.append(signal)

        elif wpm > self.max_wpm:
            # Too fast
            deviation = (wpm - self.max_wpm) / self.max_wpm
            severity = min(1.0, deviation * self.severity_scale)

            signal = create_tempo_signal(
                source=self.name,
                issue_type="too_fast",
                wpm=wpm,
                severity=severity,
                target_wpm=self.max_wpm,
            )
            signals.append(signal)

        return signals

    def _detect_pauses(
        self,
        word_timestamps: List[Dict[str, Any]]
    ) -> List[Signal]:
        """Detect long pauses between words.

        Args:
            word_timestamps: List of word timing dictionaries

        Returns:
            List of pause-related signals
        """
        signals = []

        for i in range(len(word_timestamps) - 1):
            current_end = word_timestamps[i].get('end', 0)
            next_start = word_timestamps[i + 1].get('start', 0)

            pause_duration = next_start - current_end

            if pause_duration >= self.long_pause_threshold:
                # Long pause detected
                severity = min(1.0, pause_duration / (self.long_pause_threshold * 3))

                signal = create_tempo_signal(
                    source=self.name,
                    issue_type="long_pause",
                    wpm=0.0,  # Not applicable for pauses
                    severity=severity,
                    pause_duration_sec=pause_duration,
                    pause_after_word=word_timestamps[i].get('word', ''),
                    pause_position=i,
                )
                signals.append(signal)

        return signals
