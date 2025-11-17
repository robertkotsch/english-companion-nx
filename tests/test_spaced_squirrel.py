"""Unit tests for SpacedSquirrel SRS scheduler.

Tests SM-2 algorithm, scheduling, and persistence.
"""

import json
import pytest
from pathlib import Path
from datetime import datetime, timedelta

from src.zoo.memory.spaced_squirrel import SpacedSquirrel
from src.zoo.memory.models import SRSItem


@pytest.fixture
def temp_schedule_file(tmp_path):
    """Create temporary schedule file path."""
    return str(tmp_path / "srs_schedule.json")


@pytest.fixture
def squirrel(temp_schedule_file):
    """Create SpacedSquirrel instance with temp file."""
    return SpacedSquirrel(
        schedule_file=temp_schedule_file,
        buffer_interval_sec=0  # Immediate writes for testing
    )


class TestSpacedSquirrel:
    """Test SpacedSquirrel SRS scheduler."""
    
    def test_init(self, temp_schedule_file):
        """Test initialization."""
        squirrel = SpacedSquirrel(schedule_file=temp_schedule_file)
        
        assert squirrel.schedule_file == Path(temp_schedule_file)
        assert len(squirrel._items) == 0
        assert not squirrel._dirty
    
    def test_load_schedule_missing(self, squirrel):
        """Test loading schedule when file doesn't exist."""
        result = squirrel.load_schedule()
        
        assert result is False
        assert len(squirrel._items) == 0
    
    def test_add_item(self, squirrel):
        """Test adding new SRS item."""
        item = squirrel.add_item(
            item_id="vocab_leverage",
            item_type="vocabulary",
            content="leverage (verb)"
        )
        
        assert item.id == "vocab_leverage"
        assert item.type == "vocabulary"
        assert item.interval_days == 1
        assert item.ease_factor == SpacedSquirrel.DEFAULT_EASE_FACTOR
        assert item.repetitions == 0
        assert "vocab_leverage" in squirrel._items
    
    def test_add_duplicate_item(self, squirrel):
        """Test adding duplicate item (should skip)."""
        squirrel.add_item("test_item", "vocabulary", "test")
        
        # Try to add again
        item = squirrel.add_item("test_item", "vocabulary", "test")
        
        assert item.id == "test_item"
        assert len(squirrel._items) == 1  # Still just one
    
    def test_save_and_load_schedule(self, squirrel):
        """Test saving and loading schedule."""
        # Add items
        squirrel.add_item("vocab1", "vocabulary", "word1")
        squirrel.add_item("vocab2", "vocabulary", "word2")
        squirrel.add_item("grammar1", "grammar", "pattern1")
        
        # Save
        squirrel.save_schedule(force=True)
        
        # Create new instance and load
        squirrel2 = SpacedSquirrel(schedule_file=str(squirrel.schedule_file))
        result = squirrel2.load_schedule()
        
        assert result is True
        assert len(squirrel2._items) == 3
        assert "vocab1" in squirrel2._items
        assert squirrel2._items["vocab1"].content == "word1"
    
    def test_get_due_today(self, squirrel):
        """Test getting items due today."""
        # Add item due today
        today_item = squirrel.add_item("item_today", "vocabulary", "today")
        today_item.next_review = datetime.now().isoformat()
        
        # Add item due tomorrow
        tomorrow_item = squirrel.add_item("item_tomorrow", "vocabulary", "tomorrow")
        tomorrow_item.next_review = (datetime.now() + timedelta(days=1)).isoformat()
        
        # Add item overdue
        overdue_item = squirrel.add_item("item_overdue", "vocabulary", "overdue")
        overdue_item.next_review = (datetime.now() - timedelta(days=1)).isoformat()
        
        # Get due items
        due = squirrel.get_due_today()
        
        assert len(due) == 2  # Today and overdue
        due_ids = [item.id for item in due]
        assert "item_today" in due_ids
        assert "item_overdue" in due_ids
        assert "item_tomorrow" not in due_ids
    
    def test_get_due_today_filtered(self, squirrel):
        """Test getting due items filtered by type."""
        # Add vocabulary item due today
        vocab_item = squirrel.add_item("vocab_due", "vocabulary", "vocab")
        vocab_item.next_review = datetime.now().isoformat()
        
        # Add grammar item due today
        grammar_item = squirrel.add_item("grammar_due", "grammar", "grammar")
        grammar_item.next_review = datetime.now().isoformat()
        
        # Get only vocabulary items
        vocab_due = squirrel.get_due_today(item_type="vocabulary")
        assert len(vocab_due) == 1
        assert vocab_due[0].id == "vocab_due"
        
        # Get only grammar items
        grammar_due = squirrel.get_due_today(item_type="grammar")
        assert len(grammar_due) == 1
        assert grammar_due[0].id == "grammar_due"
    
    def test_mark_reviewed_success_first_time(self, squirrel):
        """Test successful review on first attempt."""
        item = squirrel.add_item("test_item", "vocabulary", "test")
        
        # Mark as successfully reviewed
        updated = squirrel.mark_reviewed("test_item", success=True, quality=4)
        
        assert updated is not None
        assert updated.repetitions == 1
        assert updated.interval_days == 1  # First success = 1 day
        assert updated.last_review is not None
    
    def test_mark_reviewed_success_second_time(self, squirrel):
        """Test successful review on second attempt."""
        item = squirrel.add_item("test_item", "vocabulary", "test")
        
        # First review
        squirrel.mark_reviewed("test_item", success=True)
        
        # Second review
        updated = squirrel.mark_reviewed("test_item", success=True)
        
        assert updated.repetitions == 2
        assert updated.interval_days == 6  # Second success = 6 days
    
    def test_mark_reviewed_success_third_time(self, squirrel):
        """Test successful review on third attempt (uses ease factor)."""
        item = squirrel.add_item("test_item", "vocabulary", "test")
        
        # First review
        squirrel.mark_reviewed("test_item", success=True)
        
        # Second review
        squirrel.mark_reviewed("test_item", success=True)
        
        # Third review
        item = squirrel.get_item("test_item")
        original_ease = item.ease_factor
        updated = squirrel.mark_reviewed("test_item", success=True)
        
        assert updated.repetitions == 3
        # Should be 6 * ease_factor
        assert updated.interval_days == int(6 * original_ease)
    
    def test_mark_reviewed_failure(self, squirrel):
        """Test failed review (resets interval)."""
        item = squirrel.add_item("test_item", "vocabulary", "test")
        
        # First review (success)
        squirrel.mark_reviewed("test_item", success=True)
        
        # Second review (success)
        squirrel.mark_reviewed("test_item", success=True)
        
        # Third review (failure)
        updated = squirrel.mark_reviewed("test_item", success=False)
        
        assert updated.repetitions == 0  # Reset
        assert updated.interval_days == 1  # Back to initial
        assert updated.ease_factor < SpacedSquirrel.DEFAULT_EASE_FACTOR  # Decreased
    
    def test_mark_reviewed_quality_affects_ease(self, squirrel):
        """Test that quality rating affects ease factor."""
        item = squirrel.add_item("test_item", "vocabulary", "test")
        
        # Perfect recall (quality 5)
        updated = squirrel.mark_reviewed("test_item", success=True, quality=5)
        original_ease = SpacedSquirrel.DEFAULT_EASE_FACTOR
        
        # Ease factor should increase for quality 5
        assert updated.ease_factor > original_ease
    
    def test_mark_reviewed_not_found(self, squirrel):
        """Test marking non-existent item as reviewed."""
        result = squirrel.mark_reviewed("nonexistent", success=True)
        
        assert result is None
    
    def test_get_item(self, squirrel):
        """Test getting item by ID."""
        squirrel.add_item("test_item", "vocabulary", "test")
        
        item = squirrel.get_item("test_item")
        
        assert item is not None
        assert item.id == "test_item"
        
        # Non-existent
        assert squirrel.get_item("nonexistent") is None
    
    def test_get_all_items(self, squirrel):
        """Test getting all items."""
        squirrel.add_item("vocab1", "vocabulary", "word1")
        squirrel.add_item("vocab2", "vocabulary", "word2")
        squirrel.add_item("grammar1", "grammar", "pattern1")
        
        # Get all
        all_items = squirrel.get_all_items()
        assert len(all_items) == 3
        
        # Get vocabulary only
        vocab_items = squirrel.get_all_items(item_type="vocabulary")
        assert len(vocab_items) == 2
        
        # Get grammar only
        grammar_items = squirrel.get_all_items(item_type="grammar")
        assert len(grammar_items) == 1
    
    def test_get_stats(self, squirrel):
        """Test getting statistics."""
        # Add items
        squirrel.add_item("vocab1", "vocabulary", "word1")
        squirrel.add_item("grammar1", "grammar", "pattern1")
        
        # Make one due today
        item = squirrel.get_item("vocab1")
        item.next_review = datetime.now().isoformat()
        
        # Make one overdue
        item2 = squirrel.get_item("grammar1")
        item2.next_review = (datetime.now() - timedelta(days=1)).isoformat()
        
        stats = squirrel.get_stats()
        
        assert stats['total_items'] == 2
        assert stats['vocabulary_items'] == 1
        assert stats['grammar_items'] == 1
        assert stats['due_today'] == 1
        assert stats['overdue'] == 1
    
    def test_remove_item(self, squirrel):
        """Test removing item from schedule."""
        squirrel.add_item("test_item", "vocabulary", "test")
        
        assert "test_item" in squirrel._items
        
        result = squirrel.remove_item("test_item")
        
        assert result is True
        assert "test_item" not in squirrel._items
        
        # Try to remove again
        result = squirrel.remove_item("test_item")
        assert result is False
    
    def test_initialize(self, squirrel):
        """Test initialization method."""
        # Add some items and save
        squirrel.add_item("test_item", "vocabulary", "test")
        squirrel.save_schedule(force=True)
        
        # Create new instance and initialize
        squirrel2 = SpacedSquirrel(schedule_file=str(squirrel.schedule_file))
        result = squirrel2.initialize()
        
        assert result is True
        assert len(squirrel2._items) > 0
    
    def test_shutdown(self, squirrel):
        """Test shutdown saves pending changes."""
        squirrel.add_item("test_item", "vocabulary", "test")
        squirrel._dirty = True
        
        squirrel.shutdown()
        
        # Verify saved
        assert not squirrel._dirty
        assert squirrel.schedule_file.exists()
    
    def test_buffered_writes(self, temp_schedule_file):
        """Test that writes are buffered."""
        squirrel = SpacedSquirrel(
            schedule_file=temp_schedule_file,
            buffer_interval_sec=3600  # 1 hour buffer
        )
        
        squirrel.add_item("test_item", "vocabulary", "test")
        
        # Should be dirty but not saved yet
        assert squirrel._dirty
        squirrel.save_schedule()  # Try to save
        
        # Still dirty (buffer not elapsed)
        assert squirrel._dirty
        
        # Force save
        squirrel.save_schedule(force=True)
        assert not squirrel._dirty
        assert Path(temp_schedule_file).exists()
    
    def test_ease_factor_minimum(self, squirrel):
        """Test that ease factor doesn't go below minimum."""
        item = squirrel.add_item("test_item", "vocabulary", "test")
        
        # Fail multiple times
        for _ in range(10):
            squirrel.mark_reviewed("test_item", success=False)
        
        item = squirrel.get_item("test_item")
        
        # Should not go below minimum
        assert item.ease_factor >= SpacedSquirrel.MIN_EASE_FACTOR
    
    def test_interval_progression(self, squirrel):
        """Test that intervals progress correctly."""
        squirrel.add_item("test_item", "vocabulary", "test")
        
        # First success: 1 day
        squirrel.mark_reviewed("test_item", success=True)
        item = squirrel.get_item("test_item")
        assert item.interval_days == 1
        
        # Second success: 6 days
        squirrel.mark_reviewed("test_item", success=True)
        item = squirrel.get_item("test_item")
        assert item.interval_days == 6
        
        # Third success: 6 * ease_factor
        ease = item.ease_factor
        squirrel.mark_reviewed("test_item", success=True)
        item = squirrel.get_item("test_item")
        assert item.interval_days == int(6 * ease)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
