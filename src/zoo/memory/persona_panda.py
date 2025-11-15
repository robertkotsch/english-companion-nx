"""PersonaPanda - User profile and preferences manager.

Loads and manages user profile including:
- Learning goals (CEFR level, focus areas)
- Language preferences (native language, accent)
- Coaching settings (intensity, topics)
- Availability windows
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class UserProfile:
    """User profile for personalized coaching.

    Attributes:
        cefr_target: Target CEFR level (A1, A2, B1, B2, C1, C2)
        native_language: User's native language (e.g., "German")
        accent_preference: Preferred English accent ("American", "British", etc.)
        coach_intensity: Coaching mode ("off", "soft", "normal")
        weekly_focus: Current weekly focus area (e.g., "business_communication")
        topics: List of interest topics for conversation
        availability: Daily availability window {"start": "09:00", "end": "17:00"}
    """
    cefr_target: str = "C1"
    native_language: str = "German"
    accent_preference: str = "American"
    coach_intensity: str = "normal"
    weekly_focus: str = "business_communication"
    topics: List[str] = field(default_factory=lambda: ["e-learning", "3D", "leadership"])
    availability: Dict[str, str] = field(default_factory=lambda: {"start": "09:00", "end": "17:00"})

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserProfile":
        """Create profile from dictionary."""
        return cls(**data)

    def validate(self) -> bool:
        """Validate profile fields.

        Returns:
            True if valid, raises ValueError if invalid
        """
        valid_cefr = ["A1", "A2", "B1", "B2", "C1", "C2"]
        if self.cefr_target not in valid_cefr:
            raise ValueError(f"Invalid CEFR level: {self.cefr_target}, must be one of {valid_cefr}")

        valid_intensity = ["off", "soft", "normal"]
        if self.coach_intensity not in valid_intensity:
            raise ValueError(f"Invalid coach_intensity: {self.coach_intensity}, must be one of {valid_intensity}")

        if not isinstance(self.topics, list) or len(self.topics) == 0:
            raise ValueError("Topics must be a non-empty list")

        if "start" not in self.availability or "end" not in self.availability:
            raise ValueError("Availability must have 'start' and 'end' times")

        return True


class PersonaPanda:
    """User profile manager.

    Loads user profile from JSON file and provides methods to
    query and update user preferences.

    Example:
        panda = PersonaPanda(profile_path="/data/profile/user_profile.json")
        profile = panda.get_profile()
        print(f"Target level: {profile.cefr_target}")
        panda.update_intensity("soft")
    """

    DEFAULT_PROFILE = UserProfile()

    def __init__(self, profile_path: Optional[Path] = None):
        """Initialize PersonaPanda.

        Args:
            profile_path: Path to user_profile.json (creates with defaults if missing)
        """
        self._profile_path = profile_path or Path("src/data/profile/user_profile.json")
        self._profile: Optional[UserProfile] = None

        # Ensure profile directory exists
        self._profile_path.parent.mkdir(parents=True, exist_ok=True)

        # Load or create profile
        self._load_profile()

    def _load_profile(self) -> None:
        """Load profile from file or create default."""
        if self._profile_path.exists():
            try:
                with open(self._profile_path, 'r') as f:
                    data = json.load(f)
                self._profile = UserProfile.from_dict(data)
                self._profile.validate()
                logger.info(f"Loaded user profile from {self._profile_path}")
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to load profile from {self._profile_path}: {e}")
                logger.info("Using default profile")
                self._profile = self.DEFAULT_PROFILE
                self._save_profile()  # Save default to fix corruption
        else:
            logger.info(f"No profile found at {self._profile_path}, creating default")
            self._profile = self.DEFAULT_PROFILE
            self._save_profile()

    def _save_profile(self) -> None:
        """Save current profile to file."""
        try:
            with open(self._profile_path, 'w') as f:
                json.dump(self._profile.to_dict(), f, indent=2)
            logger.debug(f"Saved profile to {self._profile_path}")
        except Exception as e:
            logger.error(f"Failed to save profile: {e}")

    def get_profile(self) -> UserProfile:
        """Get the current user profile.

        Returns:
            UserProfile instance
        """
        return self._profile

    def update_intensity(self, mode: str) -> bool:
        """Update coaching intensity mode.

        Args:
            mode: New intensity ("off", "soft", "normal")

        Returns:
            True if updated, False if invalid mode
        """
        valid_modes = ["off", "soft", "normal"]
        if mode not in valid_modes:
            logger.error(f"Invalid intensity mode: {mode}, must be one of {valid_modes}")
            return False

        old_mode = self._profile.coach_intensity
        self._profile.coach_intensity = mode
        self._save_profile()

        logger.info(f"Coaching intensity updated: {old_mode} → {mode}")
        return True

    def update_weekly_focus(self, focus: str) -> None:
        """Update weekly focus area.

        Args:
            focus: New focus area (e.g., "fillers", "grammar", "vocab")
        """
        old_focus = self._profile.weekly_focus
        self._profile.weekly_focus = focus
        self._save_profile()

        logger.info(f"Weekly focus updated: {old_focus} → {focus}")

    def update_cefr_target(self, level: str) -> bool:
        """Update target CEFR level.

        Args:
            level: New CEFR level (A1-C2)

        Returns:
            True if updated, False if invalid level
        """
        valid_levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
        if level not in valid_levels:
            logger.error(f"Invalid CEFR level: {level}, must be one of {valid_levels}")
            return False

        old_level = self._profile.cefr_target
        self._profile.cefr_target = level
        self._save_profile()

        logger.info(f"CEFR target updated: {old_level} → {level}")
        return True

    def add_topic(self, topic: str) -> None:
        """Add a new interest topic.

        Args:
            topic: Topic to add
        """
        if topic not in self._profile.topics:
            self._profile.topics.append(topic)
            self._save_profile()
            logger.info(f"Added topic: {topic}")

    def remove_topic(self, topic: str) -> bool:
        """Remove an interest topic.

        Args:
            topic: Topic to remove

        Returns:
            True if removed, False if not found
        """
        if topic in self._profile.topics:
            self._profile.topics.remove(topic)
            self._save_profile()
            logger.info(f"Removed topic: {topic}")
            return True
        return False

    def get_availability_hours(self) -> tuple[int, int]:
        """Get availability as hour integers (24h format).

        Returns:
            Tuple of (start_hour, end_hour), e.g., (9, 17)
        """
        start_str = self._profile.availability.get("start", "09:00")
        end_str = self._profile.availability.get("end", "17:00")

        start_hour = int(start_str.split(":")[0])
        end_hour = int(end_str.split(":")[0])

        return start_hour, end_hour

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"PersonaPanda(level={self._profile.cefr_target}, "
            f"intensity={self._profile.coach_intensity}, "
            f"topics={len(self._profile.topics)})"
        )
