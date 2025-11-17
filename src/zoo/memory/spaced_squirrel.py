"""SpacedSquirrel - Spaced Repetition System (SRS) scheduler.

Implements simplified SM-2 algorithm for vocabulary and grammar pattern reviews.

Follows CLAUDE.md principles:
- Buffered writes (5-min intervals)
- Load once at startup, keep in RAM
- Minimal SSD writes
"""

import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from pathlib import Path

from src.zoo.memory.models import SRSItem
from src.zoo.zoo_logger import get_zoo_logger


class SpacedSquirrel:
    """SRS scheduler for vocabulary and grammar patterns.
    
    Responsibilities:
    - Schedule review items using SM-2 algorithm
    - Track review intervals and ease factors
    - Get items due for review today
    - Update schedules based on review success/failure
    
    Follows "load once, run forever" principle:
    - Loaded at service startup
    - Kept in RAM until service restarts
    - Writes buffered (5-min intervals or on shutdown)
    """
    
    # SM-2 algorithm constants
    MIN_EASE_FACTOR = 1.3
    DEFAULT_EASE_FACTOR = 2.5
    INITIAL_INTERVAL = 1  # days
    
    def __init__(
        self,
        schedule_file: str = "data/progress/srs_schedule.json",
        buffer_interval_sec: int = 300
    ):
        """Initialize SpacedSquirrel.
        
        Args:
            schedule_file: Path to SRS schedule JSON file
            buffer_interval_sec: Seconds between writes (default 300 = 5min)
        """
        self.schedule_file = Path(schedule_file)
        self.buffer_interval_sec = buffer_interval_sec
        
        # In-memory schedule (loaded once, kept in RAM)
        self._items: Dict[str, SRSItem] = {}  # item_id -> SRSItem
        self._items_by_type: Dict[str, List[str]] = {
            'vocabulary': [],
            'grammar': []
        }
        
        # Write buffer
        self._dirty = False
        self._last_save = datetime.now()
        
        # Logging
        self.logger = get_zoo_logger()
        
        # Ensure directory exists
        self.schedule_file.parent.mkdir(parents=True, exist_ok=True)
    
    def load_schedule(self) -> bool:
        """Load SRS schedule from disk into RAM.
        
        Called at startup to load existing schedule.
        Falls back to empty schedule if file doesn't exist.
        
        Returns:
            True if schedule loaded successfully, False otherwise
        """
        if not self.schedule_file.exists():
            self.logger.warning(
                "SpacedSquirrel",
                f"No schedule found at {self.schedule_file}, starting with empty schedule"
            )
            self._items = {}
            self._items_by_type = {'vocabulary': [], 'grammar': []}
            return False
        
        try:
            with open(self.schedule_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Parse items
            self._items = {}
            self._items_by_type = {'vocabulary': [], 'grammar': []}
            
            for item_data in data.get('items', []):
                item = SRSItem.from_dict(item_data)
                self._items[item.id] = item
                
                if item.type in self._items_by_type:
                    self._items_by_type[item.type].append(item.id)
            
            self.logger.info(
                "SpacedSquirrel",
                f"Loaded {len(self._items)} SRS items from schedule"
            )
            return True
            
        except Exception as e:
            self.logger.error("SpacedSquirrel", f"Failed to load schedule: {e}")
            self._items = {}
            self._items_by_type = {'vocabulary': [], 'grammar': []}
            return False
    
    def save_schedule(self, force: bool = False):
        """Save SRS schedule from RAM to disk (buffered).
        
        Only writes if:
        - force=True, OR
        - Items are dirty AND buffer interval elapsed
        
        Args:
            force: Force immediate write (used on shutdown)
        """
        if not self._dirty and not force:
            return
        
        # Check buffer interval
        elapsed = (datetime.now() - self._last_save).total_seconds()
        if not force and elapsed < self.buffer_interval_sec:
            return
        
        try:
            data = {
                'items': [item.to_dict() for item in self._items.values()],
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.schedule_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self._dirty = False
            self._last_save = datetime.now()
            
            self.logger.debug(
                "SpacedSquirrel",
                f"Saved {len(self._items)} SRS items to schedule"
            )
        except Exception as e:
            self.logger.error("SpacedSquirrel", f"Failed to save schedule: {e}")
    
    def add_item(
        self,
        item_id: str,
        item_type: str,
        content: str,
        initial_interval: int = INITIAL_INTERVAL
    ) -> SRSItem:
        """Add new item to SRS schedule.
        
        Args:
            item_id: Unique identifier
            item_type: "vocabulary" or "grammar"
            content: The word/phrase or grammar pattern
            initial_interval: Initial review interval in days
            
        Returns:
            Created SRSItem
        """
        # Check if already exists
        if item_id in self._items:
            self.logger.warning(
                "SpacedSquirrel",
                f"Item {item_id} already exists, skipping"
            )
            return self._items[item_id]
        
        # Calculate next review date
        next_review = (datetime.now() + timedelta(days=initial_interval)).isoformat()
        
        item = SRSItem(
            id=item_id,
            type=item_type,
            content=content,
            interval_days=initial_interval,
            next_review=next_review,
            ease_factor=self.DEFAULT_EASE_FACTOR,
            repetitions=0,
            last_review=None
        )
        
        self._items[item_id] = item
        
        if item_type in self._items_by_type:
            self._items_by_type[item_type].append(item_id)
        
        self._dirty = True
        
        self.logger.info(
            "SpacedSquirrel",
            f"Added SRS item: {item_id} ({item_type}), next review in {initial_interval}d"
        )
        
        return item
    
    def get_due_today(self, item_type: Optional[str] = None) -> List[SRSItem]:
        """Get items due for review today.
        
        Args:
            item_type: Filter by type ("vocabulary", "grammar"), or None for all
            
        Returns:
            List of SRSItems due today
        """
        today = datetime.now().date()
        due_items = []
        
        for item in self._items.values():
            # Filter by type if specified
            if item_type and item.type != item_type:
                continue
            
            # Check if due today or overdue
            try:
                next_review_date = datetime.fromisoformat(item.next_review).date()
                if next_review_date <= today:
                    due_items.append(item)
            except Exception as e:
                self.logger.warning(
                    "SpacedSquirrel",
                    f"Invalid date for item {item.id}: {e}"
                )
        
        return due_items
    
    def mark_reviewed(
        self,
        item_id: str,
        success: bool,
        quality: int = 3
    ) -> Optional[SRSItem]:
        """Mark item as reviewed and update schedule using SM-2 algorithm.
        
        SM-2 Algorithm:
        - Quality: 0-5 (0=complete failure, 5=perfect recall)
        - If quality >= 3: Success, increase interval
        - If quality < 3: Failure, restart interval
        
        Args:
            item_id: Item ID to update
            success: True if review was successful
            quality: SM-2 quality rating (0-5), default 3 for simple success
            
        Returns:
            Updated SRSItem, or None if not found
        """
        if item_id not in self._items:
            self.logger.warning("SpacedSquirrel", f"Item {item_id} not found")
            return None
        
        item = self._items[item_id]
        
        # Update last review
        item.last_review = datetime.now().isoformat()
        
        if success and quality >= 3:
            # Successful review - increase interval
            if item.repetitions == 0:
                item.interval_days = 1
            elif item.repetitions == 1:
                item.interval_days = 6
            else:
                item.interval_days = int(item.interval_days * item.ease_factor)
            
            item.repetitions += 1
            
            # Update ease factor based on quality
            item.ease_factor = max(
                self.MIN_EASE_FACTOR,
                item.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
            )
            
            self.logger.info(
                "SpacedSquirrel",
                f"✅ {item_id}: Success, next review in {item.interval_days}d"
            )
        else:
            # Failed review - restart interval
            item.interval_days = self.INITIAL_INTERVAL
            item.repetitions = 0
            item.ease_factor = max(self.MIN_EASE_FACTOR, item.ease_factor - 0.2)
            
            self.logger.info(
                "SpacedSquirrel",
                f"❌ {item_id}: Failed, restarting interval"
            )
        
        # Calculate next review date
        item.next_review = (
            datetime.now() + timedelta(days=item.interval_days)
        ).isoformat()
        
        self._dirty = True
        self.save_schedule()  # Buffered save
        
        return item
    
    def get_item(self, item_id: str) -> Optional[SRSItem]:
        """Get SRS item by ID.
        
        Args:
            item_id: Item ID
            
        Returns:
            SRSItem if found, None otherwise
        """
        return self._items.get(item_id)
    
    def get_all_items(self, item_type: Optional[str] = None) -> List[SRSItem]:
        """Get all SRS items.
        
        Args:
            item_type: Filter by type, or None for all
            
        Returns:
            List of all SRSItems
        """
        if item_type is None:
            return list(self._items.values())
        
        item_ids = self._items_by_type.get(item_type, [])
        return [self._items[item_id] for item_id in item_ids if item_id in self._items]
    
    def get_stats(self) -> Dict[str, int]:
        """Get SRS statistics.
        
        Returns:
            Dictionary with statistics
        """
        today = datetime.now().date()
        
        stats = {
            'total_items': len(self._items),
            'vocabulary_items': len(self._items_by_type.get('vocabulary', [])),
            'grammar_items': len(self._items_by_type.get('grammar', [])),
            'due_today': 0,
            'overdue': 0
        }
        
        for item in self._items.values():
            try:
                next_review = datetime.fromisoformat(item.next_review).date()
                if next_review == today:
                    stats['due_today'] += 1
                elif next_review < today:
                    stats['overdue'] += 1
            except:
                pass
        
        return stats
    
    def remove_item(self, item_id: str) -> bool:
        """Remove item from schedule.
        
        Args:
            item_id: Item ID to remove
            
        Returns:
            True if removed, False if not found
        """
        if item_id not in self._items:
            return False
        
        item = self._items[item_id]
        
        # Remove from type index
        if item.type in self._items_by_type:
            if item_id in self._items_by_type[item.type]:
                self._items_by_type[item.type].remove(item_id)
        
        # Remove from main dict
        del self._items[item_id]
        
        self._dirty = True
        self.save_schedule()
        
        self.logger.info("SpacedSquirrel", f"Removed SRS item: {item_id}")
        return True
    
    def initialize(self) -> bool:
        """Initialize agent at startup.
        
        Loads schedule from disk.
        Called once at DAY_BOOT.
        
        Returns:
            True if initialized successfully
        """
        self.logger.info("SpacedSquirrel", "Initializing...")
        
        self.load_schedule()
        
        # Log statistics
        stats = self.get_stats()
        self.logger.info(
            "SpacedSquirrel",
            f"Loaded {stats['total_items']} items "
            f"({stats['due_today']} due today, {stats['overdue']} overdue)"
        )
        
        return True
    
    def shutdown(self):
        """Shutdown agent - force save any pending changes."""
        self.logger.info("SpacedSquirrel", "Shutting down, saving schedule...")
        self.save_schedule(force=True)
