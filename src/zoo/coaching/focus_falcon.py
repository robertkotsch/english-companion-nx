"""FocusFalcon - Focus area selector for daily sessions.

Selects and rotates focus areas (grammar/fillers/vocab) based on recent performance.

Follows CLAUDE.md principles:
- Load once at DAY_BOOT
- Simple decision-making logic
- No heavy models
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict
from pathlib import Path
import json

from src.zoo.zoo_logger import get_zoo_logger


class FocusFalcon:
    """Focus area selection agent.
    
    Responsibilities:
    - Select daily focus area (grammar/fillers/vocab)
    - Rotate focus to avoid repetition
    - Consider recent performance stats (when available)
    - Respect user preferences from PersonaPanda
    
    Follows "load once, run forever" principle:
    - Loaded at service startup
    - Keeps state in RAM
    - Simple rotation logic
    """
    
    # Available focus areas
    FOCUS_AREAS = ['grammar', 'fillers', 'vocab']
    
    # Focus rotation tracking file
    ROTATION_FILE = "data/progress/focus_rotation.json"
    
    def __init__(
        self,
        persona_panda=None,  # PersonaPanda instance (optional)
        history_file: str = ROTATION_FILE
    ):
        """Initialize FocusFalcon.
        
        Args:
            persona_panda: PersonaPanda instance for user preferences
            history_file: Path to focus rotation history
        """
        self.persona_panda = persona_panda
        self.history_file = Path(history_file)
        
        # Focus history (last N days)
        self._focus_history: List[Dict] = []  # [{date, focus}, ...]
        self._current_focus: Optional[str] = None
        
        # Logging
        self.logger = get_zoo_logger()
        
        # Ensure directory exists
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
    
    def load_history(self) -> bool:
        """Load focus rotation history from disk.
        
        Returns:
            True if history loaded successfully
        """
        if not self.history_file.exists():
            self.logger.info(
                "FocusFalcon",
                "No focus history found, starting fresh"
            )
            self._focus_history = []
            return False
        
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._focus_history = data.get('history', [])
            
            self.logger.info(
                "FocusFalcon",
                f"Loaded {len(self._focus_history)} days of focus history"
            )
            return True
            
        except Exception as e:
            self.logger.error("FocusFalcon", f"Failed to load history: {e}")
            self._focus_history = []
            return False
    
    def save_history(self):
        """Save focus rotation history to disk."""
        try:
            # Keep only last 30 days
            if len(self._focus_history) > 30:
                self._focus_history = self._focus_history[-30:]
            
            data = {
                'history': self._focus_history,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            self.logger.debug("FocusFalcon", "Saved focus history")
        except Exception as e:
            self.logger.error("FocusFalcon", f"Failed to save history: {e}")
    
    def _get_recent_focuses(self, days: int = 7) -> List[str]:
        """Get focus areas from recent days.
        
        Args:
            days: Number of recent days to check
            
        Returns:
            List of focus areas from recent days
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).date()
        recent = []
        
        for entry in self._focus_history:
            try:
                entry_date = datetime.fromisoformat(entry['date']).date()
                if entry_date >= cutoff_date:
                    recent.append(entry['focus'])
            except Exception:
                pass
        
        return recent
    
    def _count_focus_occurrences(self, days: int = 7) -> Dict[str, int]:
        """Count how many times each focus appeared recently.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dictionary mapping focus area to count
        """
        recent = self._get_recent_focuses(days)
        counts = {focus: 0 for focus in self.FOCUS_AREAS}
        
        for focus in recent:
            if focus in counts:
                counts[focus] += 1
        
        return counts
    
    def _get_least_used_focus(self) -> str:
        """Get the focus area used least recently.
        
        Returns:
            Focus area to prioritize
        """
        counts = self._count_focus_occurrences(days=7)
        
        # Find minimum count
        min_count = min(counts.values())
        
        # Get all areas with minimum count
        candidates = [focus for focus, count in counts.items() if count == min_count]
        
        # If multiple candidates, prefer based on priority order
        # Default priority: grammar > vocab > fillers
        priority_order = ['grammar', 'vocab', 'fillers']
        
        for preferred in priority_order:
            if preferred in candidates:
                return preferred
        
        return candidates[0]
    
    def select_focus(
        self,
        stats: Optional[Dict] = None,
        force_focus: Optional[str] = None
    ) -> str:
        """Select focus area for today.
        
        Selection logic:
        1. If force_focus provided, use it
        2. If PersonaPanda has weekly_focus set, use it
        3. Otherwise, rotate based on least-used area
        
        Args:
            stats: Optional recent stats (error rates, filler rates, etc.)
            force_focus: Force specific focus area
            
        Returns:
            Selected focus area
        """
        # Option 1: Forced focus (for testing or manual override)
        if force_focus and force_focus in self.FOCUS_AREAS:
            self._current_focus = force_focus
            self.logger.info("FocusFalcon", f"Using forced focus: {force_focus}")
            return force_focus
        
        # Option 2: User preference from PersonaPanda
        if self.persona_panda:
            try:
                profile = self.persona_panda.get_profile()
                weekly_focus = profile.weekly_focus
                
                # Map weekly_focus to our focus areas
                focus_mapping = {
                    'grammar': 'grammar',
                    'vocabulary': 'vocab',
                    'fluency': 'fillers',  # Fluency work = reduce fillers
                    'business_communication': 'vocab'  # Focus on vocabulary
                }
                
                if weekly_focus in focus_mapping:
                    mapped_focus = focus_mapping[weekly_focus]
                    self._current_focus = mapped_focus
                    self.logger.info(
                        "FocusFalcon",
                        f"Using user preference: {mapped_focus} (from {weekly_focus})"
                    )
                    return mapped_focus
            except Exception as e:
                self.logger.warning(
                    "FocusFalcon",
                    f"Could not get user preference: {e}"
                )
        
        # Option 3: Rotate based on least-used area
        focus = self._get_least_used_focus()
        self._current_focus = focus
        
        recent_counts = self._count_focus_occurrences(days=7)
        self.logger.info(
            "FocusFalcon",
            f"Selected focus: {focus} (recent usage: {recent_counts})"
        )
        
        # Record selection
        self._record_focus(focus)
        
        return focus
    
    def _record_focus(self, focus: str):
        """Record today's focus selection in history.
        
        Args:
            focus: Selected focus area
        """
        today = datetime.now().date().isoformat()
        
        # Check if today already recorded (avoid duplicates)
        for entry in self._focus_history:
            if entry.get('date') == today:
                # Update existing entry
                entry['focus'] = focus
                self.save_history()
                return
        
        # Add new entry
        self._focus_history.append({
            'date': today,
            'focus': focus
        })
        
        self.save_history()
    
    def should_rotate(self) -> bool:
        """Check if focus should be rotated.
        
        Logic: Rotate if same focus used for 3+ consecutive days
        
        Returns:
            True if rotation recommended
        """
        recent = self._get_recent_focuses(days=3)
        
        if len(recent) < 3:
            return False
        
        # Check if all 3 are the same
        if len(set(recent)) == 1:
            self.logger.info(
                "FocusFalcon",
                f"Rotation recommended: {recent[-1]} used for 3 days"
            )
            return True
        
        return False
    
    def get_current_focus(self) -> Optional[str]:
        """Get currently selected focus area.
        
        Returns:
            Current focus area, or None if not set
        """
        return self._current_focus
    
    def get_focus_history(self, days: int = 7) -> List[Dict]:
        """Get focus history for recent days.
        
        Args:
            days: Number of days to retrieve
            
        Returns:
            List of focus history entries
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).date()
        recent = []
        
        for entry in self._focus_history:
            try:
                entry_date = datetime.fromisoformat(entry['date']).date()
                if entry_date >= cutoff_date:
                    recent.append(entry)
            except Exception:
                pass
        
        return recent
    
    def get_stats(self) -> Dict:
        """Get focus rotation statistics.
        
        Returns:
            Dictionary with statistics
        """
        counts_7d = self._count_focus_occurrences(days=7)
        counts_30d = self._count_focus_occurrences(days=30)
        
        return {
            'current_focus': self._current_focus,
            'should_rotate': self.should_rotate(),
            'usage_last_7d': counts_7d,
            'usage_last_30d': counts_30d,
            'history_size': len(self._focus_history)
        }
    
    def initialize(self) -> bool:
        """Initialize agent at startup.
        
        Loads focus history and prepares for selection.
        Called once at DAY_BOOT.
        
        Returns:
            True if initialized successfully
        """
        self.logger.info("FocusFalcon", "Initializing...")
        
        # Load history
        self.load_history()
        
        # Select focus will be called by SessionShepherd when building daily plan
        
        return True
    
    def reset_history(self):
        """Reset focus history (for testing or reset purposes)."""
        self.logger.warning("FocusFalcon", "Resetting focus history")
        self._focus_history = []
        self._current_focus = None
        self.save_history()
