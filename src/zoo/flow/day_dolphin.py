"""DayDolphin - Daily session state machine.

Manages the flow of the coaching day:
DAY_BOOT → WAITING_FOR_USER → IN_SESSION ⇄ FREE_CONVERSATION → DAY_OVER
"""

from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime, time as dt_time
import logging

logger = logging.getLogger(__name__)


class DayState(Enum):
    """States in the daily coaching cycle."""
    DAY_BOOT = "day_boot"              # Service starts, initializing plan
    WAITING_FOR_USER = "waiting"       # Plan ready, waiting for first utterance
    IN_SESSION = "in_session"          # Structured session active (quick/full)
    FREE_CONVERSATION = "free"         # Casual chat, signals passive
    DAY_OVER = "day_over"              # After hours or shutdown


class SessionType(Enum):
    """Types of structured sessions."""
    QUICK = "quick"      # 5-7 minutes, focused drills
    FULL = "full"        # 15-20 minutes, comprehensive
    FREE = "free"        # No structure, pure conversation


class DayDolphin:
    """State machine for managing daily coaching flow.

    Responsibilities:
    - Track current state in the daily cycle
    - Validate state transitions
    - Enforce time-based boundaries (9am-5pm)
    - Manage session lifecycle

    Example:
        dolphin = DayDolphin(start_hour=9, end_hour=17)
        dolphin.boot()  # → WAITING_FOR_USER
        dolphin.start_session(SessionType.QUICK)  # → IN_SESSION
        dolphin.end_session()  # → WAITING_FOR_USER
    """

    def __init__(
        self,
        start_hour: int = 9,
        end_hour: int = 17,
        initial_state: DayState = DayState.DAY_BOOT
    ):
        """Initialize DayDolphin.

        Args:
            start_hour: Daily start time (24h format, e.g., 9 for 9am)
            end_hour: Daily end time (24h format, e.g., 17 for 5pm)
            initial_state: Starting state (default: DAY_BOOT)
        """
        self._state = initial_state
        self._session_type: Optional[SessionType] = None
        self._session_start: Optional[datetime] = None
        self._start_time = dt_time(hour=start_hour)
        self._end_time = dt_time(hour=end_hour)

        logger.info(
            f"DayDolphin initialized: {start_hour}:00-{end_hour}:00, state={initial_state.value}"
        )

    @property
    def state(self) -> DayState:
        """Get current state."""
        return self._state

    @property
    def session_type(self) -> Optional[SessionType]:
        """Get current session type (None if not in session)."""
        return self._session_type

    @property
    def session_duration_seconds(self) -> Optional[float]:
        """Get current session duration in seconds (None if not in session)."""
        if self._session_start is None:
            return None
        return (datetime.now() - self._session_start).total_seconds()

    def is_within_hours(self) -> bool:
        """Check if current time is within coaching hours."""
        now = datetime.now().time()
        return self._start_time <= now <= self._end_time

    def boot(self) -> None:
        """Initialize the day.

        Transitions: DAY_BOOT → WAITING_FOR_USER
        """
        if self._state != DayState.DAY_BOOT:
            logger.warning(f"boot() called from {self._state.value}, expected DAY_BOOT")

        if not self.is_within_hours():
            logger.warning("boot() called outside coaching hours, transitioning to DAY_OVER")
            self._transition_to(DayState.DAY_OVER)
            return

        logger.info("Day initialized, waiting for user")
        self._transition_to(DayState.WAITING_FOR_USER)

    def start_session(self, session_type: SessionType) -> bool:
        """Start a structured or free session.

        Args:
            session_type: Type of session to start

        Returns:
            True if session started, False if rejected

        Transitions:
            WAITING_FOR_USER → IN_SESSION (if structured)
            WAITING_FOR_USER → FREE_CONVERSATION (if free)
            IN_SESSION → IN_SESSION (session type change)
            FREE_CONVERSATION → IN_SESSION (upgrade to structured)
        """
        if self._state == DayState.DAY_OVER:
            logger.error("Cannot start session: day is over")
            return False

        if not self.is_within_hours():
            logger.warning("Session start attempted outside coaching hours")
            self._transition_to(DayState.DAY_OVER)
            return False

        # End any existing session first
        if self._state == DayState.IN_SESSION:
            logger.info(f"Ending current {self._session_type.value} session before starting new one")
            self._end_session_internal()

        self._session_type = session_type
        self._session_start = datetime.now()

        if session_type == SessionType.FREE:
            self._transition_to(DayState.FREE_CONVERSATION)
            logger.info("Free conversation started")
        else:
            self._transition_to(DayState.IN_SESSION)
            logger.info(f"{session_type.value.capitalize()} session started")

        return True

    def end_session(self) -> bool:
        """End the current session.

        Returns:
            True if session ended, False if no session active

        Transitions: IN_SESSION/FREE_CONVERSATION → WAITING_FOR_USER
        """
        if self._state not in (DayState.IN_SESSION, DayState.FREE_CONVERSATION):
            logger.warning(f"end_session() called from {self._state.value}, no session active")
            return False

        self._end_session_internal()
        return True

    def _end_session_internal(self) -> None:
        """Internal session cleanup."""
        duration = self.session_duration_seconds
        session_info = f"{self._session_type.value if self._session_type else 'unknown'}"
        if duration:
            session_info += f" ({duration:.1f}s)"

        logger.info(f"Session ended: {session_info}")

        self._session_type = None
        self._session_start = None

        if self.is_within_hours():
            self._transition_to(DayState.WAITING_FOR_USER)
        else:
            self._transition_to(DayState.DAY_OVER)

    def transition_to_free(self) -> bool:
        """Switch from structured session to free conversation.

        Returns:
            True if transitioned, False if rejected

        Transitions: IN_SESSION → FREE_CONVERSATION
        """
        if self._state != DayState.IN_SESSION:
            logger.warning(f"transition_to_free() called from {self._state.value}, expected IN_SESSION")
            return False

        logger.info(f"Switching from {self._session_type.value} session to free conversation")
        self._session_type = SessionType.FREE
        self._transition_to(DayState.FREE_CONVERSATION)
        return True

    def shutdown(self) -> None:
        """Shut down the day (end of day or service stop).

        Transitions: ANY → DAY_OVER
        """
        if self._state == DayState.IN_SESSION or self._state == DayState.FREE_CONVERSATION:
            logger.info("Ending active session before shutdown")
            self._end_session_internal()

        logger.info("Day shutting down")
        self._transition_to(DayState.DAY_OVER)

    def _transition_to(self, new_state: DayState) -> None:
        """Internal state transition with logging.

        Args:
            new_state: Target state
        """
        old_state = self._state
        self._state = new_state
        logger.debug(f"State transition: {old_state.value} → {new_state.value}")

    def get_state_info(self) -> Dict[str, Any]:
        """Get current state information for logging/debugging.

        Returns:
            Dictionary with state details
        """
        return {
            "state": self._state.value,
            "session_type": self._session_type.value if self._session_type else None,
            "session_duration_sec": self.session_duration_seconds,
            "within_hours": self.is_within_hours(),
            "coaching_hours": f"{self._start_time.hour}:00-{self._end_time.hour}:00",
        }

    def __repr__(self) -> str:
        """String representation."""
        session_info = f", session={self._session_type.value}" if self._session_type else ""
        return f"DayDolphin(state={self._state.value}{session_info})"
