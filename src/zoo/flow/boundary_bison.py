"""BoundaryBison agent for flow control and intensity management.

BoundaryBison ensures the user isn't overwhelmed by drills by enforcing
rate limits based on the current coaching mode.
"""

import time
from typing import Literal

# Coaching Modes
MODE_OFF = "off"
MODE_SOFT = "soft"
MODE_NORMAL = "normal"

class BoundaryBison:
    """Agent responsible for managing coaching intensity."""

    def __init__(self, initial_mode: str = MODE_NORMAL):
        """
        Args:
            initial_mode: Starting coaching mode.
        """
        self.mode = initial_mode
        self.last_drill_time = 0.0
        
        # Rate limits (seconds between drills)
        self.rate_limits = {
            MODE_OFF: float('inf'),  # Never drill
            MODE_SOFT: 300.0,        # 5 minutes
            MODE_NORMAL: 60.0        # 1 minute
        }

    def set_mode(self, mode: str):
        """Update the coaching mode."""
        if mode not in [MODE_OFF, MODE_SOFT, MODE_NORMAL]:
            print(f"BoundaryBison Warning: Invalid mode '{mode}'. Keeping '{self.mode}'.")
            return
        self.mode = mode
        print(f"BoundaryBison: Mode set to {self.mode}")

    def get_mode(self) -> str:
        """Return current mode."""
        return self.mode

    def can_drill_now(self) -> bool:
        """Check if a drill is allowed right now based on rate limits.
        
        Returns:
            True if allowed, False otherwise.
        """
        if self.mode == MODE_OFF:
            return False
            
        now = time.time()
        min_interval = self.rate_limits.get(self.mode, 60.0)
        
        if now - self.last_drill_time >= min_interval:
            return True
            
        return False

    def record_drill(self):
        """Record that a drill has just been delivered."""
        self.last_drill_time = time.time()
