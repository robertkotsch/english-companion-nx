"""Zoo system configuration.

Loads and manages configuration for Zoo agents from environment variables
with sensible defaults for Jetson Orin NX constraints.
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class ZooConfig:
    """Zoo system configuration.

    All settings can be overridden via environment variables.
    """

    # System control
    enabled: bool = True
    coach_mode: str = "normal"  # "off" | "soft" | "normal"
    daily_start: str = "09:00"
    daily_end: str = "17:00"

    # Notion integration
    notion_api_key: Optional[str] = None
    notion_vocab_db_id: Optional[str] = None
    notion_sync_interval_hours: int = 24

    # Orchestrator settings
    orchestrator_max_drills_per_min: int = 1
    orchestrator_drill_cooldown_sec: int = 60

    # Listener thresholds
    filler_threshold_per_min: float = 3.0
    tempo_min_wpm: int = 100
    tempo_max_wpm: int = 180
    grammar_severity_threshold: float = 0.5

    # Memory constraints (Jetson-specific)
    max_context_exchanges: int = 20
    log_flush_interval_sec: int = 300  # 5 minutes
    session_buffer_size: int = 100

    # File paths
    data_dir: str = "src/data"
    vocab_cache_dir: str = "src/data/vocab"
    progress_dir: str = "src/data/progress"
    profile_dir: str = "src/data/profile"
    session_logs_dir: str = "logs/sessions"

    @classmethod
    def from_env(cls) -> "ZooConfig":
        """Load configuration from environment variables.

        Returns:
            ZooConfig instance with values from env or defaults
        """
        return cls(
            # System control
            enabled=os.getenv("ZOO_ENABLED", "true").lower() == "true",
            coach_mode=os.getenv("ZOO_COACH_MODE", "normal"),
            daily_start=os.getenv("ZOO_DAILY_START", "09:00"),
            daily_end=os.getenv("ZOO_DAILY_END", "17:00"),

            # Notion integration
            notion_api_key=os.getenv("NOTION_API_KEY"),
            notion_vocab_db_id=os.getenv("NOTION_VOCAB_DB_ID"),
            notion_sync_interval_hours=int(os.getenv("NOTION_SYNC_INTERVAL_HOURS", "24")),

            # Orchestrator settings
            orchestrator_max_drills_per_min=int(os.getenv("ORCHESTRATOR_MAX_DRILLS_PER_MIN", "1")),
            orchestrator_drill_cooldown_sec=int(os.getenv("ORCHESTRATOR_DRILL_COOLDOWN_SEC", "60")),

            # Listener thresholds
            filler_threshold_per_min=float(os.getenv("FILLER_THRESHOLD_PER_MIN", "3.0")),
            tempo_min_wpm=int(os.getenv("TEMPO_MIN_WPM", "100")),
            tempo_max_wpm=int(os.getenv("TEMPO_MAX_WPM", "180")),
            grammar_severity_threshold=float(os.getenv("GRAMMAR_SEVERITY_THRESHOLD", "0.5")),

            # Memory constraints
            max_context_exchanges=int(os.getenv("ZOO_MAX_CONTEXT_EXCHANGES", "20")),
            log_flush_interval_sec=int(os.getenv("ZOO_LOG_FLUSH_INTERVAL_SEC", "300")),
            session_buffer_size=int(os.getenv("ZOO_SESSION_BUFFER_SIZE", "100")),

            # File paths
            data_dir=os.getenv("ZOO_DATA_DIR", "src/data"),
            vocab_cache_dir=os.getenv("ZOO_VOCAB_CACHE_DIR", "src/data/vocab"),
            progress_dir=os.getenv("ZOO_PROGRESS_DIR", "src/data/progress"),
            profile_dir=os.getenv("ZOO_PROFILE_DIR", "src/data/profile"),
            session_logs_dir=os.getenv("ZOO_SESSION_LOGS_DIR", "logs/sessions"),
        )

    def validate(self) -> bool:
        """Validate configuration values.

        Returns:
            True if valid

        Raises:
            ValueError if any setting is invalid
        """
        # Validate coach mode
        valid_modes = ["off", "soft", "normal"]
        if self.coach_mode not in valid_modes:
            raise ValueError(f"Invalid coach_mode: {self.coach_mode}, must be one of {valid_modes}")

        # Validate time format (HH:MM)
        for time_str, name in [(self.daily_start, "daily_start"), (self.daily_end, "daily_end")]:
            try:
                hours, mins = time_str.split(":")
                if not (0 <= int(hours) <= 23 and 0 <= int(mins) <= 59):
                    raise ValueError
            except (ValueError, AttributeError):
                raise ValueError(f"Invalid {name}: {time_str}, must be HH:MM format")

        # Validate thresholds
        if self.filler_threshold_per_min < 0:
            raise ValueError(f"filler_threshold_per_min must be >= 0, got {self.filler_threshold_per_min}")

        if self.tempo_min_wpm >= self.tempo_max_wpm:
            raise ValueError(f"tempo_min_wpm ({self.tempo_min_wpm}) must be < tempo_max_wpm ({self.tempo_max_wpm})")

        if not 0.0 <= self.grammar_severity_threshold <= 1.0:
            raise ValueError(f"grammar_severity_threshold must be 0.0-1.0, got {self.grammar_severity_threshold}")

        # Validate memory constraints
        if self.max_context_exchanges < 1:
            raise ValueError(f"max_context_exchanges must be >= 1, got {self.max_context_exchanges}")

        if self.log_flush_interval_sec < 10:
            raise ValueError(f"log_flush_interval_sec must be >= 10, got {self.log_flush_interval_sec}")

        return True

    def get_daily_hours(self) -> tuple[int, int]:
        """Parse daily start/end times as hour integers.

        Returns:
            Tuple of (start_hour, end_hour) in 24h format
        """
        start_hour = int(self.daily_start.split(":")[0])
        end_hour = int(self.daily_end.split(":")[0])
        return start_hour, end_hour

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ZooConfig(enabled={self.enabled}, mode={self.coach_mode}, "
            f"hours={self.daily_start}-{self.daily_end})"
        )


# Global config instance (lazy-loaded)
_global_config: Optional[ZooConfig] = None


def get_zoo_config() -> ZooConfig:
    """Get the global Zoo configuration instance.

    Lazy-loads configuration from environment on first call.

    Returns:
        ZooConfig instance
    """
    global _global_config
    if _global_config is None:
        _global_config = ZooConfig.from_env()
        _global_config.validate()
    return _global_config


def reload_zoo_config() -> ZooConfig:
    """Force reload configuration from environment.

    Useful for testing or dynamic config changes.

    Returns:
        New ZooConfig instance
    """
    global _global_config
    _global_config = ZooConfig.from_env()
    _global_config.validate()
    return _global_config
