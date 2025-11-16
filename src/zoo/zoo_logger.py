"""Zoo logging system with visual output for agent activity.

Provides dedicated logging for Zoo agents with emoji markers and
clear formatting for visibility during conversations.
"""

import logging
import sys
from typing import Optional, List
from datetime import datetime


class ZooLogger:
    """Dedicated logger for Zoo agent system.

    Provides visual, structured logging for agent activity during conversations.
    Each agent type has distinctive visual markers for easy identification.
    """

    # Animal emoji markers for each agent type
    MARKERS = {
        # Listeners
        'FillerFalcon': '🦅',
        'TempoTiger': '🐅',
        'GrammarGiraffe': '🦒',
        'LexiLynx': '🐆',

        # Orchestrator (Phase 1.4)
        'OrchestratorOctopus': '🐙',

        # Memory (Phase 1.3)
        'NotionNightingale': '🐦',
        'SpacedSquirrel': '🐿️',
        'PersonaPanda': '🐼',

        # Coaching (Phase 1.5)
        'CoachCoyote': '🐺',
        'TaskTiger': '🐯',
        'SessionShepherd': '🐑',
        'FocusFalcon': '🦜',

        # Flow (Phase 1.6)
        'DayDolphin': '🐬',
        'ScribeSparrow': '🐦‍⬛',
        'BoundaryBison': '🦬',

        # Generic
        'Zoo': '🏞️',
    }

    def __init__(
        self,
        name: str = "Zoo",
        level: int = logging.INFO,
        show_timestamps: bool = True,
        colorize: bool = True
    ):
        """Initialize Zoo logger.

        Args:
            name: Logger name (default: "Zoo")
            level: Logging level (default: INFO)
            show_timestamps: Include timestamps in output
            colorize: Use ANSI color codes (disable for file logging)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.show_timestamps = show_timestamps
        self.colorize = colorize

        # Prevent duplicate handlers
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(level)
            formatter = logging.Formatter('%(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def _format_message(
        self,
        agent_name: str,
        message: str,
        level: str = "INFO"
    ) -> str:
        """Format message with agent marker and optional timestamp.

        Args:
            agent_name: Name of the agent
            message: Log message
            level: Log level (INFO, DEBUG, WARNING, ERROR)

        Returns:
            Formatted log message
        """
        # Get emoji marker
        marker = self.MARKERS.get(agent_name, '🔹')

        # Build message parts
        parts = []

        # Optional timestamp
        if self.show_timestamps:
            timestamp = datetime.now().strftime("%H:%M:%S")
            parts.append(f"[{timestamp}]")

        # Level color (if enabled)
        if self.colorize:
            level_colors = {
                'DEBUG': '\033[36m',    # Cyan
                'INFO': '\033[32m',     # Green
                'WARNING': '\033[33m',  # Yellow
                'ERROR': '\033[31m',    # Red
            }
            reset = '\033[0m'
            color = level_colors.get(level, '')
            parts.append(f"{color}{marker} {agent_name}{reset}")
        else:
            parts.append(f"{marker} {agent_name}")

        parts.append(message)

        return " | ".join(parts)

    def listener_started(self, agent_name: str):
        """Log listener processing started."""
        msg = self._format_message(agent_name, "Processing utterance...", "DEBUG")
        self.logger.debug(msg)

    def listener_signal(
        self,
        agent_name: str,
        signal_type: str,
        severity: float,
        details: str = ""
    ):
        """Log signal emission from listener.

        Args:
            agent_name: Name of listener agent
            signal_type: Type of signal emitted
            severity: Signal severity (0.0-1.0)
            details: Optional details about the signal
        """
        severity_label = "🔴" if severity > 0.7 else "🟡" if severity > 0.4 else "🟢"
        msg = f"Signal: {signal_type} {severity_label} ({severity:.2f})"
        if details:
            msg += f" - {details}"

        formatted = self._format_message(agent_name, msg, "INFO")
        self.logger.info(formatted)

    def listener_no_signal(self, agent_name: str):
        """Log that listener found no issues."""
        msg = self._format_message(agent_name, "✓ No issues detected", "DEBUG")
        self.logger.debug(msg)

    def listener_error(self, agent_name: str, error: str):
        """Log listener processing error."""
        msg = self._format_message(agent_name, f"❌ Error: {error}", "ERROR")
        self.logger.error(msg)

    def orchestrator_decision(
        self,
        action: str,
        signal_count: int,
        details: str = ""
    ):
        """Log orchestrator decision.

        Args:
            action: Action taken (DRILL_NOW, BUFFER, IGNORE, PASS_THROUGH)
            signal_count: Number of signals processed
            details: Optional details about decision
        """
        msg = f"Decision: {action} ({signal_count} signals)"
        if details:
            msg += f" - {details}"

        formatted = self._format_message("OrchestratorOctopus", msg, "INFO")
        self.logger.info(formatted)

    def coach_response(self, agent_name: str, response_type: str, details: str = ""):
        """Log coach agent response."""
        msg = f"Response: {response_type}"
        if details:
            msg += f" - {details}"

        formatted = self._format_message(agent_name, msg, "INFO")
        self.logger.info(formatted)

    def memory_update(self, agent_name: str, update_type: str, details: str = ""):
        """Log memory agent update."""
        msg = f"Update: {update_type}"
        if details:
            msg += f" - {details}"

        formatted = self._format_message(agent_name, msg, "INFO")
        self.logger.info(formatted)

    def phase_transition(self, from_phase: str, to_phase: str):
        """Log day phase transition."""
        msg = f"Phase: {from_phase} → {to_phase}"
        formatted = self._format_message("DayDolphin", msg, "INFO")
        self.logger.info(formatted)

    def session_event(self, event_type: str, details: str = ""):
        """Log session-level events."""
        msg = f"Session: {event_type}"
        if details:
            msg += f" - {details}"

        formatted = self._format_message("SessionShepherd", msg, "INFO")
        self.logger.info(formatted)

    def separator(self, title: Optional[str] = None):
        """Print a visual separator."""
        if title:
            line = f"{'=' * 20} {title} {'=' * 20}"
        else:
            line = "=" * 60
        self.logger.info(line)

    def summary(self, title: str, items: List[str]):
        """Print a summary section.

        Args:
            title: Summary section title
            items: List of summary items
        """
        self.separator(title)
        for item in items:
            self.logger.info(f"  • {item}")
        self.separator()

    # Convenience methods
    def info(self, agent_name: str, message: str):
        """Generic info log."""
        msg = self._format_message(agent_name, message, "INFO")
        self.logger.info(msg)

    def debug(self, agent_name: str, message: str):
        """Generic debug log."""
        msg = self._format_message(agent_name, message, "DEBUG")
        self.logger.debug(msg)

    def warning(self, agent_name: str, message: str):
        """Generic warning log."""
        msg = self._format_message(agent_name, message, "WARNING")
        self.logger.warning(msg)

    def error(self, agent_name: str, message: str):
        """Generic error log."""
        msg = self._format_message(agent_name, message, "ERROR")
        self.logger.error(msg)


# Global logger instance
_global_logger: Optional[ZooLogger] = None


def get_zoo_logger(
    level: int = logging.INFO,
    show_timestamps: bool = True,
    colorize: bool = True
) -> ZooLogger:
    """Get or create global Zoo logger instance.

    Args:
        level: Logging level (only used on first call)
        show_timestamps: Show timestamps (only used on first call)
        colorize: Use colors (only used on first call)

    Returns:
        Global ZooLogger instance
    """
    global _global_logger

    if _global_logger is None:
        _global_logger = ZooLogger(
            name="Zoo",
            level=level,
            show_timestamps=show_timestamps,
            colorize=colorize
        )

    return _global_logger


def set_zoo_log_level(level: int):
    """Set Zoo logger level.

    Args:
        level: Logging level (logging.DEBUG, INFO, WARNING, ERROR)
    """
    logger = get_zoo_logger()
    logger.logger.setLevel(level)
    for handler in logger.logger.handlers:
        handler.setLevel(level)
