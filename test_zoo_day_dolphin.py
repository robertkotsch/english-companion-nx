"""Unit tests for DayDolphin state machine."""

import pytest
import time
from datetime import datetime, time as dt_time
from unittest.mock import patch
from src.zoo.flow.day_dolphin import DayDolphin, DayState, SessionType


class TestDayDolphinInit:
    """Tests for DayDolphin initialization."""

    def test_default_init(self):
        """Test default initialization."""
        dolphin = DayDolphin()

        assert dolphin.state == DayState.DAY_BOOT
        assert dolphin.session_type is None
        assert dolphin.session_duration_seconds is None

    def test_custom_hours_init(self):
        """Test initialization with custom hours."""
        dolphin = DayDolphin(start_hour=8, end_hour=18)

        assert dolphin.state == DayState.DAY_BOOT
        info = dolphin.get_state_info()
        assert info["coaching_hours"] == "8:00-18:00"

    def test_custom_initial_state(self):
        """Test initialization with custom initial state."""
        dolphin = DayDolphin(initial_state=DayState.WAITING_FOR_USER)

        assert dolphin.state == DayState.WAITING_FOR_USER


class TestDayDolphinBoot:
    """Tests for boot sequence."""

    @patch('src.zoo.flow.day_dolphin.datetime')
    def test_boot_within_hours(self, mock_datetime):
        """Test boot during coaching hours."""
        # Mock time to 10:00 AM
        mock_datetime.now.return_value = datetime(2024, 12, 15, 10, 0)

        dolphin = DayDolphin(start_hour=9, end_hour=17)
        dolphin.boot()

        assert dolphin.state == DayState.WAITING_FOR_USER

    @patch('src.zoo.flow.day_dolphin.datetime')
    def test_boot_outside_hours(self, mock_datetime):
        """Test boot outside coaching hours."""
        # Mock time to 8:00 AM (before start)
        mock_datetime.now.return_value = datetime(2024, 12, 15, 8, 0)

        dolphin = DayDolphin(start_hour=9, end_hour=17)
        dolphin.boot()

        assert dolphin.state == DayState.DAY_OVER

    @patch('src.zoo.flow.day_dolphin.datetime')
    def test_boot_at_boundary(self, mock_datetime):
        """Test boot exactly at start time."""
        # Mock time to 9:00 AM
        mock_datetime.now.return_value = datetime(2024, 12, 15, 9, 0)

        dolphin = DayDolphin(start_hour=9, end_hour=17)
        dolphin.boot()

        assert dolphin.state == DayState.WAITING_FOR_USER


class TestDayDolphinSessions:
    """Tests for session management."""

    @patch('src.zoo.flow.day_dolphin.datetime')
    def test_start_quick_session(self, mock_datetime):
        """Test starting a quick session."""
        mock_datetime.now.return_value = datetime(2024, 12, 15, 10, 0)

        dolphin = DayDolphin(start_hour=9, end_hour=17)
        dolphin.boot()

        result = dolphin.start_session(SessionType.QUICK)

        assert result is True
        assert dolphin.state == DayState.IN_SESSION
        assert dolphin.session_type == SessionType.QUICK
        assert dolphin.session_duration_seconds is not None

    @patch('src.zoo.flow.day_dolphin.datetime')
    def test_start_full_session(self, mock_datetime):
        """Test starting a full session."""
        mock_datetime.now.return_value = datetime(2024, 12, 15, 10, 0)

        dolphin = DayDolphin(start_hour=9, end_hour=17)
        dolphin.boot()

        result = dolphin.start_session(SessionType.FULL)

        assert result is True
        assert dolphin.state == DayState.IN_SESSION
        assert dolphin.session_type == SessionType.FULL

    @patch('src.zoo.flow.day_dolphin.datetime')
    def test_start_free_conversation(self, mock_datetime):
        """Test starting free conversation."""
        mock_datetime.now.return_value = datetime(2024, 12, 15, 10, 0)

        dolphin = DayDolphin(start_hour=9, end_hour=17)
        dolphin.boot()

        result = dolphin.start_session(SessionType.FREE)

        assert result is True
        assert dolphin.state == DayState.FREE_CONVERSATION
        assert dolphin.session_type == SessionType.FREE

    @patch('src.zoo.flow.day_dolphin.datetime')
    def test_start_session_when_day_over(self, mock_datetime):
        """Test starting session after day is over."""
        mock_datetime.now.return_value = datetime(2024, 12, 15, 18, 0)

        dolphin = DayDolphin(start_hour=9, end_hour=17)
        dolphin.boot()  # Will transition to DAY_OVER

        result = dolphin.start_session(SessionType.QUICK)

        assert result is False
        assert dolphin.state == DayState.DAY_OVER

    @patch('src.zoo.flow.day_dolphin.datetime')
    def test_end_session(self, mock_datetime):
        """Test ending a session."""
        mock_datetime.now.return_value = datetime(2024, 12, 15, 10, 0)

        dolphin = DayDolphin(start_hour=9, end_hour=17)
        dolphin.boot()
        dolphin.start_session(SessionType.QUICK)

        result = dolphin.end_session()

        assert result is True
        assert dolphin.state == DayState.WAITING_FOR_USER
        assert dolphin.session_type is None
        assert dolphin.session_duration_seconds is None

    @patch('src.zoo.flow.day_dolphin.datetime')
    def test_end_session_when_none_active(self, mock_datetime):
        """Test ending session when none is active."""
        mock_datetime.now.return_value = datetime(2024, 12, 15, 10, 0)

        dolphin = DayDolphin(start_hour=9, end_hour=17)
        dolphin.boot()

        result = dolphin.end_session()

        assert result is False
        assert dolphin.state == DayState.WAITING_FOR_USER

    @patch('src.zoo.flow.day_dolphin.datetime')
    def test_session_type_change(self, mock_datetime):
        """Test changing session type while in session."""
        mock_datetime.now.return_value = datetime(2024, 12, 15, 10, 0)

        dolphin = DayDolphin(start_hour=9, end_hour=17)
        dolphin.boot()
        dolphin.start_session(SessionType.QUICK)

        # Switch to full session
        result = dolphin.start_session(SessionType.FULL)

        assert result is True
        assert dolphin.state == DayState.IN_SESSION
        assert dolphin.session_type == SessionType.FULL


class TestDayDolphinTransitions:
    """Tests for state transitions."""

    @patch('src.zoo.flow.day_dolphin.datetime')
    def test_transition_to_free(self, mock_datetime):
        """Test transitioning from structured session to free conversation."""
        mock_datetime.now.return_value = datetime(2024, 12, 15, 10, 0)

        dolphin = DayDolphin(start_hour=9, end_hour=17)
        dolphin.boot()
        dolphin.start_session(SessionType.QUICK)

        result = dolphin.transition_to_free()

        assert result is True
        assert dolphin.state == DayState.FREE_CONVERSATION
        assert dolphin.session_type == SessionType.FREE

    @patch('src.zoo.flow.day_dolphin.datetime')
    def test_transition_to_free_from_waiting(self, mock_datetime):
        """Test invalid transition to free from waiting state."""
        mock_datetime.now.return_value = datetime(2024, 12, 15, 10, 0)

        dolphin = DayDolphin(start_hour=9, end_hour=17)
        dolphin.boot()

        result = dolphin.transition_to_free()

        assert result is False
        assert dolphin.state == DayState.WAITING_FOR_USER

    @patch('src.zoo.flow.day_dolphin.datetime')
    def test_shutdown(self, mock_datetime):
        """Test shutdown from any state."""
        mock_datetime.now.return_value = datetime(2024, 12, 15, 10, 0)

        dolphin = DayDolphin(start_hour=9, end_hour=17)
        dolphin.boot()
        dolphin.start_session(SessionType.FULL)

        dolphin.shutdown()

        assert dolphin.state == DayState.DAY_OVER
        assert dolphin.session_type is None

    @patch('src.zoo.flow.day_dolphin.datetime')
    def test_shutdown_from_waiting(self, mock_datetime):
        """Test shutdown from waiting state."""
        mock_datetime.now.return_value = datetime(2024, 12, 15, 10, 0)

        dolphin = DayDolphin(start_hour=9, end_hour=17)
        dolphin.boot()

        dolphin.shutdown()

        assert dolphin.state == DayState.DAY_OVER


class TestDayDolphinSessionDuration:
    """Tests for session duration tracking."""

    @patch('src.zoo.flow.day_dolphin.datetime')
    def test_session_duration_tracking(self, mock_datetime):
        """Test session duration calculation."""
        # Start session at 10:00
        start_time = datetime(2024, 12, 15, 10, 0, 0)
        mock_datetime.now.return_value = start_time

        dolphin = DayDolphin(start_hour=9, end_hour=17)
        dolphin.boot()
        dolphin.start_session(SessionType.QUICK)

        # Move time forward 5 minutes
        mock_datetime.now.return_value = datetime(2024, 12, 15, 10, 5, 0)

        duration = dolphin.session_duration_seconds
        assert duration == pytest.approx(300.0, rel=1)  # 5 minutes = 300 seconds

    def test_session_duration_none_when_no_session(self):
        """Test session duration is None when no session active."""
        dolphin = DayDolphin(start_hour=9, end_hour=17)

        assert dolphin.session_duration_seconds is None


class TestDayDolphinStateInfo:
    """Tests for state information retrieval."""

    @patch('src.zoo.flow.day_dolphin.datetime')
    def test_get_state_info(self, mock_datetime):
        """Test getting state information."""
        mock_datetime.now.return_value = datetime(2024, 12, 15, 10, 0)

        dolphin = DayDolphin(start_hour=9, end_hour=17)
        dolphin.boot()
        dolphin.start_session(SessionType.QUICK)

        info = dolphin.get_state_info()

        assert info["state"] == "in_session"
        assert info["session_type"] == "quick"
        assert info["session_duration_sec"] is not None
        assert info["within_hours"] is True
        assert info["coaching_hours"] == "9:00-17:00"

    @patch('src.zoo.flow.day_dolphin.datetime')
    def test_repr(self, mock_datetime):
        """Test string representation."""
        mock_datetime.now.return_value = datetime(2024, 12, 15, 10, 0)

        dolphin = DayDolphin(start_hour=9, end_hour=17)
        dolphin.boot()
        dolphin.start_session(SessionType.FULL)

        repr_str = repr(dolphin)

        assert "DayDolphin" in repr_str
        assert "in_session" in repr_str
        assert "full" in repr_str


class TestDayDolphinBoundaryConditions:
    """Tests for edge cases and boundary conditions."""

    @patch('src.zoo.flow.day_dolphin.datetime')
    def test_end_session_outside_hours(self, mock_datetime):
        """Test ending session after coaching hours end."""
        # Start session at 16:30
        mock_datetime.now.return_value = datetime(2024, 12, 15, 16, 30)

        dolphin = DayDolphin(start_hour=9, end_hour=17)
        dolphin.boot()
        dolphin.start_session(SessionType.QUICK)

        # End session at 17:30 (after hours)
        mock_datetime.now.return_value = datetime(2024, 12, 15, 17, 30)

        dolphin.end_session()

        # Should transition to DAY_OVER instead of WAITING_FOR_USER
        assert dolphin.state == DayState.DAY_OVER

    @patch('src.zoo.flow.day_dolphin.datetime')
    def test_start_session_exactly_at_end_time(self, mock_datetime):
        """Test starting session exactly at end time."""
        # Exactly 17:00
        mock_datetime.now.return_value = datetime(2024, 12, 15, 17, 0)

        dolphin = DayDolphin(start_hour=9, end_hour=17)
        dolphin.boot()

        # Should still be within hours (inclusive)
        result = dolphin.start_session(SessionType.QUICK)
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
