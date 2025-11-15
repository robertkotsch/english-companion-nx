"""Unit tests for Zoo signal system."""

import pytest
import time
from src.zoo.signals import (
    Signal,
    create_grammar_signal,
    create_filler_signal,
    create_vocab_signal,
    create_tempo_signal,
    SIGNAL_GRAMMAR_ERROR,
    SIGNAL_FILLER_DETECTED,
    SIGNAL_VOCAB_OPPORTUNITY,
    SIGNAL_VOCAB_USED,
    SIGNAL_TEMPO_ISSUE,
)


class TestSignal:
    """Tests for Signal dataclass."""

    def test_signal_creation(self):
        """Test basic signal creation."""
        signal = Signal(
            source="TestAgent",
            type="test_signal",
            severity=0.5,
            scope="utterance",
            realtime_desirable=True,
            data={"key": "value"}
        )

        assert signal.source == "TestAgent"
        assert signal.type == "test_signal"
        assert signal.severity == 0.5
        assert signal.scope == "utterance"
        assert signal.realtime_desirable is True
        assert signal.data == {"key": "value"}
        assert isinstance(signal.timestamp, float)
        assert isinstance(signal.utterance_id, str)

    def test_signal_severity_validation(self):
        """Test severity range validation."""
        # Valid severities
        Signal(
            source="Test",
            type="test",
            severity=0.0,
            scope="utterance",
            realtime_desirable=False,
            data={}
        )
        Signal(
            source="Test",
            type="test",
            severity=1.0,
            scope="utterance",
            realtime_desirable=False,
            data={}
        )

        # Invalid severities
        with pytest.raises(ValueError, match="Severity must be 0.0-1.0"):
            Signal(
                source="Test",
                type="test",
                severity=-0.1,
                scope="utterance",
                realtime_desirable=False,
                data={}
            )

        with pytest.raises(ValueError, match="Severity must be 0.0-1.0"):
            Signal(
                source="Test",
                type="test",
                severity=1.1,
                scope="utterance",
                realtime_desirable=False,
                data={}
            )

    def test_signal_scope_validation(self):
        """Test scope value validation."""
        # Valid scopes
        for scope in ["utterance", "session", "trend"]:
            Signal(
                source="Test",
                type="test",
                severity=0.5,
                scope=scope,
                realtime_desirable=False,
                data={}
            )

        # Invalid scope
        with pytest.raises(ValueError, match="Invalid scope"):
            Signal(
                source="Test",
                type="test",
                severity=0.5,
                scope="invalid",
                realtime_desirable=False,
                data={}
            )

    def test_signal_to_dict(self):
        """Test signal serialization to dict."""
        signal = Signal(
            source="TestAgent",
            type="test_signal",
            severity=0.7,
            scope="session",
            realtime_desirable=True,
            data={"count": 5}
        )

        d = signal.to_dict()

        assert d["source"] == "TestAgent"
        assert d["type"] == "test_signal"
        assert d["severity"] == 0.7
        assert d["scope"] == "session"
        assert d["realtime_desirable"] is True
        assert d["data"] == {"count": 5}
        assert "timestamp" in d
        assert "utterance_id" in d

    def test_signal_from_dict(self):
        """Test signal deserialization from dict."""
        data = {
            "source": "TestAgent",
            "type": "test_signal",
            "severity": 0.3,
            "scope": "trend",
            "realtime_desirable": False,
            "data": {"metric": 42},
            "timestamp": 1234567890.0,
            "utterance_id": "test-uuid-123",
        }

        signal = Signal.from_dict(data)

        assert signal.source == "TestAgent"
        assert signal.type == "test_signal"
        assert signal.severity == 0.3
        assert signal.scope == "trend"
        assert signal.realtime_desirable is False
        assert signal.data == {"metric": 42}
        assert signal.timestamp == 1234567890.0
        assert signal.utterance_id == "test-uuid-123"


class TestGrammarSignal:
    """Tests for grammar signal factory."""

    def test_create_grammar_signal(self):
        """Test grammar signal creation."""
        signal = create_grammar_signal(
            source="GrammarGiraffe",
            error_type="articles",
            severity=0.8,
            original="I have dog",
            suggestion="I have a dog"
        )

        assert signal.source == "GrammarGiraffe"
        assert signal.type == SIGNAL_GRAMMAR_ERROR
        assert signal.severity == 0.8
        assert signal.scope == "utterance"
        assert signal.realtime_desirable is True  # severity > 0.7
        assert signal.data["error_type"] == "articles"
        assert signal.data["original"] == "I have dog"
        assert signal.data["suggestion"] == "I have a dog"

    def test_grammar_signal_low_severity(self):
        """Test grammar signal with low severity doesn't trigger realtime."""
        signal = create_grammar_signal(
            source="GrammarGiraffe",
            error_type="minor",
            severity=0.3,
            original="test",
        )

        assert signal.realtime_desirable is False


class TestFillerSignal:
    """Tests for filler signal factory."""

    def test_create_filler_signal(self):
        """Test filler signal creation."""
        signal = create_filler_signal(
            source="FillerFalcon",
            filler_word="um",
            position=3,
            total_count=2,
            rate_per_min=5.0
        )

        assert signal.source == "FillerFalcon"
        assert signal.type == SIGNAL_FILLER_DETECTED
        assert signal.severity == 0.5  # rate 5.0 / 10.0
        assert signal.scope == "utterance"
        assert signal.realtime_desirable is False  # count < 3
        assert signal.data["filler"] == "um"
        assert signal.data["position"] == 3
        assert signal.data["count"] == 2
        assert signal.data["rate_per_min"] == 5.0

    def test_filler_signal_high_count(self):
        """Test filler signal with high count triggers realtime."""
        signal = create_filler_signal(
            source="FillerFalcon",
            filler_word="like",
            position=5,
            total_count=3,
            rate_per_min=8.0
        )

        assert signal.realtime_desirable is True  # count >= 3

    def test_filler_signal_severity_capping(self):
        """Test filler severity is capped at 1.0."""
        signal = create_filler_signal(
            source="FillerFalcon",
            filler_word="uh",
            position=0,
            total_count=1,
            rate_per_min=20.0  # Would be 2.0 without cap
        )

        assert signal.severity == 1.0


class TestVocabSignal:
    """Tests for vocabulary signal factory."""

    def test_create_vocab_used_signal(self):
        """Test vocab_used signal creation."""
        signal = create_vocab_signal(
            source="LexiLynx",
            signal_type=SIGNAL_VOCAB_USED,
            word="leverage",
            severity=0.0,  # Positive usage = low severity
            correct=True
        )

        assert signal.source == "LexiLynx"
        assert signal.type == SIGNAL_VOCAB_USED
        assert signal.severity == 0.0
        assert signal.scope == "utterance"
        assert signal.realtime_desirable is False
        assert signal.data["word"] == "leverage"
        assert signal.data["correct"] is True

    def test_create_vocab_opportunity_signal(self):
        """Test vocab_opportunity signal creation."""
        signal = create_vocab_signal(
            source="LexiLynx",
            signal_type=SIGNAL_VOCAB_OPPORTUNITY,
            word="facilitate",
            severity=0.8,
            context="Could have used 'facilitate' here"
        )

        assert signal.type == SIGNAL_VOCAB_OPPORTUNITY
        assert signal.severity == 0.8
        assert signal.realtime_desirable is True  # severity > 0.6
        assert signal.data["word"] == "facilitate"
        assert signal.data["context"] == "Could have used 'facilitate' here"


class TestTempoSignal:
    """Tests for tempo signal factory."""

    def test_create_tempo_signal_slow(self):
        """Test tempo signal for slow speech."""
        signal = create_tempo_signal(
            source="TempoTiger",
            issue_type="too_slow",
            wpm=85.0,
            severity=0.4,
        )

        assert signal.source == "TempoTiger"
        assert signal.type == SIGNAL_TEMPO_ISSUE
        assert signal.severity == 0.4
        assert signal.scope == "session"  # Session-level metric
        assert signal.realtime_desirable is False  # Don't interrupt
        assert signal.data["issue_type"] == "too_slow"
        assert signal.data["wpm"] == 85.0

    def test_create_tempo_signal_long_pause(self):
        """Test tempo signal for long pauses."""
        signal = create_tempo_signal(
            source="TempoTiger",
            issue_type="long_pause",
            wpm=120.0,
            severity=0.6,
            pause_duration_sec=3.5,
            pause_position=15
        )

        assert signal.data["issue_type"] == "long_pause"
        assert signal.data["pause_duration_sec"] == 3.5
        assert signal.data["pause_position"] == 15


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
