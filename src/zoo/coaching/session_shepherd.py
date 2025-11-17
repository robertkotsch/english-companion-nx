"""SessionShepherd - Daily session planner and coordinator.

Builds daily practice plans based on SRS reviews and focus areas.
Selects appropriate session types (quick/full/free).

Follows CLAUDE.md principles:
- Load once at DAY_BOOT
- Keep plan in RAM for the day
- Minimal SSD writes
"""

from datetime import datetime
from typing import List, Optional, Dict
from pathlib import Path
import json

from src.zoo.memory.models import DailyPlan, SessionPlan
from src.zoo.zoo_logger import get_zoo_logger


class SessionShepherd:
    """Session planning and coordination agent.
    
    Responsibilities:
    - Build daily practice plan at DAY_BOOT
    - Select session subset based on type (quick/full/free)
    - Track completion of planned items
    - Provide session recommendations
    
    Follows "load once, run forever" principle:
    - Creates plan at startup
    - Keeps plan in RAM until service restarts
    - Updates completion status in memory
    """
    
    # Session type configurations
    SESSION_CONFIGS = {
        'quick': {
            'duration_target_min': 7,
            'max_review_items': 3,
            'drill_budget': 3
        },
        'full': {
            'duration_target_min': 20,
            'max_review_items': 7,
            'drill_budget': 10
        },
        'free': {
            'duration_target_min': None,  # No limit
            'max_review_items': 0,  # No structured reviews
            'drill_budget': 15  # Still allow drills if triggered
        }
    }
    
    def __init__(
        self,
        spaced_squirrel,  # SpacedSquirrel instance
        focus_falcon,     # FocusFalcon instance
        plan_file: str = "data/progress/daily_plan.json"
    ):
        """Initialize SessionShepherd.
        
        Args:
            spaced_squirrel: SpacedSquirrel instance for SRS items
            focus_falcon: FocusFalcon instance for focus selection
            plan_file: Path to save daily plan (optional)
        """
        self.spaced_squirrel = spaced_squirrel
        self.focus_falcon = focus_falcon
        self.plan_file = Path(plan_file)
        
        # Current daily plan (loaded once at boot)
        self._daily_plan: Optional[DailyPlan] = None
        self._completed_items: List[str] = []  # Item IDs completed today
        self._sessions_today: int = 0
        
        # Logging
        self.logger = get_zoo_logger()
        
        # Ensure directory exists
        self.plan_file.parent.mkdir(parents=True, exist_ok=True)
    
    def build_daily_plan(self) -> DailyPlan:
        """Build daily practice plan at DAY_BOOT.
        
        Process:
        1. Get items due today from SpacedSquirrel
        2. Get focus area from FocusFalcon
        3. Build session plans for each type
        
        Returns:
            DailyPlan for today
        """
        today = datetime.now().date().isoformat()
        
        self.logger.info("SessionShepherd", "Building daily plan...")
        
        # Get SRS items due today
        due_items = self.spaced_squirrel.get_due_today()
        due_item_ids = [item.id for item in due_items]
        
        self.logger.info(
            "SessionShepherd",
            f"Found {len(due_items)} items due for review today"
        )
        
        # Get focus area for today
        focus = self.focus_falcon.select_focus()
        
        self.logger.info("SessionShepherd", f"Today's focus: {focus}")
        
        # Get vocabulary targets (items with status "learning")
        vocab_targets = []
        all_vocab = self.spaced_squirrel.get_all_items(item_type="vocabulary")
        for item in all_vocab[:10]:  # Top 10 most relevant
            vocab_targets.append(item.id)
        
        # Build session plans for each type
        session_plans = {}
        
        for session_type, config in self.SESSION_CONFIGS.items():
            # Select subset of review items based on session type
            max_reviews = config['max_review_items']
            review_items = due_item_ids[:max_reviews] if max_reviews > 0 else []
            
            session_plans[session_type] = SessionPlan(
                session_type=session_type,
                duration_target_min=config['duration_target_min'] or 0,
                focus=focus,
                review_items=review_items,
                drill_budget=config['drill_budget'],
                vocab_targets=vocab_targets[:5] if session_type != 'free' else []
            )
        
        # Create daily plan
        self._daily_plan = DailyPlan(
            date=today,
            focus=focus,
            review_due=due_item_ids,
            session_plans=session_plans
        )
        
        # Save plan to disk (optional, for reference)
        self._save_plan()
        
        self.logger.info(
            "SessionShepherd",
            f"Daily plan created: {len(due_item_ids)} items due, focus on {focus}"
        )
        
        return self._daily_plan
    
    def _save_plan(self):
        """Save current daily plan to disk (optional)."""
        if self._daily_plan is None:
            return
        
        try:
            with open(self.plan_file, 'w', encoding='utf-8') as f:
                json.dump(self._daily_plan.to_dict(), f, indent=2)
            
            self.logger.debug("SessionShepherd", "Saved daily plan to disk")
        except Exception as e:
            self.logger.warning("SessionShepherd", f"Failed to save plan: {e}")
    
    def get_session_plan(self, session_type: str = 'quick') -> SessionPlan:
        """Get session plan for specified type.
        
        Args:
            session_type: "quick", "full", or "free"
            
        Returns:
            SessionPlan for the requested type
        """
        if self._daily_plan is None:
            self.logger.warning(
                "SessionShepherd",
                "No daily plan available, building on-demand..."
            )
            self.build_daily_plan()
        
        plan = self._daily_plan.session_plans.get(session_type)
        
        if plan is None:
            self.logger.warning(
                "SessionShepherd",
                f"Unknown session type: {session_type}, defaulting to 'quick'"
            )
            plan = self._daily_plan.session_plans.get('quick')
        
        self._sessions_today += 1
        
        self.logger.info(
            "SessionShepherd",
            f"Session {self._sessions_today}: {session_type} "
            f"({plan.duration_target_min}min, {len(plan.review_items)} reviews)"
        )
        
        return plan
    
    def mark_item_completed(self, item_id: str):
        """Mark review item as completed.
        
        Args:
            item_id: SRS item ID that was reviewed
        """
        if item_id not in self._completed_items:
            self._completed_items.append(item_id)
            
            self.logger.info(
                "SessionShepherd",
                f"Marked {item_id} as completed "
                f"({len(self._completed_items)}/{len(self._daily_plan.review_due)} done)"
            )
    
    def get_completion_status(self) -> Dict[str, any]:
        """Get today's completion status.
        
        Returns:
            Dictionary with completion statistics
        """
        if self._daily_plan is None:
            return {
                'total_due': 0,
                'completed': 0,
                'remaining': 0,
                'completion_rate': 0.0,
                'sessions_today': self._sessions_today
            }
        
        total_due = len(self._daily_plan.review_due)
        completed = len(self._completed_items)
        remaining = total_due - completed
        completion_rate = (completed / total_due * 100) if total_due > 0 else 0.0
        
        return {
            'total_due': total_due,
            'completed': completed,
            'remaining': remaining,
            'completion_rate': completion_rate,
            'sessions_today': self._sessions_today
        }
    
    def get_remaining_items(self) -> List[str]:
        """Get list of remaining (not yet completed) review items.
        
        Returns:
            List of item IDs not yet completed
        """
        if self._daily_plan is None:
            return []
        
        return [
            item_id for item_id in self._daily_plan.review_due
            if item_id not in self._completed_items
        ]
    
    def suggest_session_type(self) -> str:
        """Suggest appropriate session type based on current state.
        
        Logic:
        - If many items remaining: suggest 'full'
        - If few items remaining: suggest 'quick'
        - If all items done: suggest 'free'
        
        Returns:
            Suggested session type
        """
        if self._daily_plan is None:
            return 'quick'
        
        remaining = self.get_remaining_items()
        
        if len(remaining) == 0:
            return 'free'
        elif len(remaining) > 5:
            return 'full'
        else:
            return 'quick'
    
    def get_daily_plan(self) -> Optional[DailyPlan]:
        """Get current daily plan.
        
        Returns:
            Current DailyPlan, or None if not built yet
        """
        return self._daily_plan
    
    def reset_day(self):
        """Reset daily tracking (called at DAY_OVER or new DAY_BOOT).
        
        This would typically be called when transitioning to a new day.
        """
        self.logger.info("SessionShepherd", "Resetting day...")
        
        self._daily_plan = None
        self._completed_items = []
        self._sessions_today = 0
    
    def initialize(self) -> bool:
        """Initialize agent at startup.
        
        Builds daily plan for today.
        Called once at DAY_BOOT.
        
        Returns:
            True if initialized successfully
        """
        self.logger.info("SessionShepherd", "Initializing...")
        
        # Build today's plan
        self.build_daily_plan()
        
        # Log summary
        status = self.get_completion_status()
        self.logger.info(
            "SessionShepherd",
            f"Initialized: {status['total_due']} items due, "
            f"focus on {self._daily_plan.focus}"
        )
        
        return self._daily_plan is not None
    
    def get_session_summary(self) -> str:
        """Get human-readable session summary.
        
        Returns:
            Summary string for display
        """
        if self._daily_plan is None:
            return "No active plan"
        
        status = self.get_completion_status()
        
        summary_parts = [
            f"Today: {self._daily_plan.focus}",
            f"Progress: {status['completed']}/{status['total_due']} reviews done",
            f"Sessions: {status['sessions_today']} today"
        ]
        
        if status['remaining'] > 0:
            suggestion = self.suggest_session_type()
            summary_parts.append(f"Suggest: {suggestion} session next")
        else:
            summary_parts.append("All reviews complete! 🎉")
        
        return " | ".join(summary_parts)
