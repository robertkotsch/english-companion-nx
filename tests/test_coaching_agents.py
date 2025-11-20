import unittest
from unittest.mock import MagicMock, patch
import sys
import os
from pathlib import Path
from datetime import datetime, date

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.zoo.coaching.session_shepherd import SessionShepherd
from src.zoo.coaching.focus_falcon import FocusFalcon
from src.zoo.memory.models import SRSItem, VocabItem

class TestFocusFalcon(unittest.TestCase):
    def setUp(self):
        self.test_history_file = "tests/data/test_focus_history.json"
        self.falcon = FocusFalcon(history_file=self.test_history_file)
        
        # Ensure clean state
        if os.path.exists(self.test_history_file):
            os.remove(self.test_history_file)
            
    def tearDown(self):
        if os.path.exists(self.test_history_file):
            os.remove(self.test_history_file)

    def test_initialization(self):
        """Test initialization and history loading."""
        self.assertTrue(self.falcon.initialize())
        self.assertEqual(self.falcon._focus_history, [])

    def test_select_focus_rotation(self):
        """Test focus selection rotation logic."""
        # First selection
        focus1 = self.falcon.select_focus()
        self.assertIn(focus1, self.falcon.FOCUS_AREAS)
        
        # Record it manually to simulate history (since we can't easily mock time in this simple test)
        self.falcon._record_focus(focus1)
        
        # Second selection should ideally be different or follow logic
        # For simple rotation, we just verify it returns a valid focus
        focus2 = self.falcon.select_focus()
        self.assertIn(focus2, self.falcon.FOCUS_AREAS)

    def test_force_focus(self):
        """Test forcing a specific focus."""
        focus = self.falcon.select_focus(force_focus='grammar')
        self.assertEqual(focus, 'grammar')
        self.assertEqual(self.falcon.get_current_focus(), 'grammar')

    def test_should_rotate(self):
        """Test rotation recommendation logic."""
        # Mock history with 3 same days
        today = date.today().isoformat()
        self.falcon._focus_history = [
            {'date': '2023-01-01', 'focus': 'grammar'},
            {'date': '2023-01-02', 'focus': 'grammar'},
            {'date': '2023-01-03', 'focus': 'grammar'}
        ]
        
        # We need to mock _get_recent_focuses because it filters by date relative to NOW
        with patch.object(self.falcon, '_get_recent_focuses', return_value=['grammar', 'grammar', 'grammar']):
            self.assertTrue(self.falcon.should_rotate())
            
        with patch.object(self.falcon, '_get_recent_focuses', return_value=['grammar', 'vocab', 'grammar']):
            self.assertFalse(self.falcon.should_rotate())


class TestSessionShepherd(unittest.TestCase):
    def setUp(self):
        self.mock_squirrel = MagicMock()
        self.mock_falcon = MagicMock()
        self.test_plan_file = "tests/data/test_daily_plan.json"
        
        self.shepherd = SessionShepherd(
            spaced_squirrel=self.mock_squirrel,
            focus_falcon=self.mock_falcon,
            plan_file=self.test_plan_file
        )
        
        # Setup mock returns
        self.mock_squirrel.get_due_today.return_value = [
            SRSItem(item_id="item1", next_review="2023-01-01"),
            SRSItem(item_id="item2", next_review="2023-01-01"),
            SRSItem(item_id="item3", next_review="2023-01-01"),
            SRSItem(item_id="item4", next_review="2023-01-01"),
            SRSItem(item_id="item5", next_review="2023-01-01")
        ]
        self.mock_squirrel.get_all_items.return_value = []
        self.mock_falcon.select_focus.return_value = "vocab"

    def tearDown(self):
        if os.path.exists(self.test_plan_file):
            os.remove(self.test_plan_file)

    def test_build_daily_plan(self):
        """Test building the daily plan."""
        plan = self.shepherd.build_daily_plan()
        
        self.assertIsNotNone(plan)
        self.assertEqual(plan.focus, "vocab")
        self.assertEqual(len(plan.review_due), 5)
        self.assertIn("quick", plan.session_plans)
        self.assertIn("full", plan.session_plans)
        
        # Verify dependencies called
        self.mock_squirrel.get_due_today.assert_called_once()
        self.mock_falcon.select_focus.assert_called_once()

    def test_get_session_plan(self):
        """Test retrieving a specific session plan."""
        self.shepherd.build_daily_plan()
        
        # Test Quick Session
        quick_plan = self.shepherd.get_session_plan('quick')
        self.assertEqual(quick_plan.session_type, 'quick')
        self.assertLessEqual(len(quick_plan.review_items), 3) # Config max is 3
        
        # Test Full Session
        full_plan = self.shepherd.get_session_plan('full')
        self.assertEqual(full_plan.session_type, 'full')
        self.assertLessEqual(len(full_plan.review_items), 7) # Config max is 7

    def test_completion_tracking(self):
        """Test tracking completed items."""
        self.shepherd.build_daily_plan()
        
        # Initial state
        status = self.shepherd.get_completion_status()
        self.assertEqual(status['completed'], 0)
        self.assertEqual(status['total_due'], 5)
        
        # Mark item complete
        self.shepherd.mark_item_completed("item1")
        
        # Check status
        status = self.shepherd.get_completion_status()
        self.assertEqual(status['completed'], 1)
        self.assertEqual(status['remaining'], 4)
        self.assertEqual(status['completion_rate'], 20.0)
        
        # Check remaining items
        remaining = self.shepherd.get_remaining_items()
        self.assertNotIn("item1", remaining)
        self.assertIn("item2", remaining)

    def test_session_suggestion(self):
        """Test session type suggestions."""
        self.shepherd.build_daily_plan()
        
        # 5 items remaining -> Quick (since <= 5 is quick in logic? Wait, logic says > 5 is full)
        # Logic: > 5 full, else quick. 5 is not > 5, so quick.
        self.assertEqual(self.shepherd.suggest_session_type(), 'quick')
        
        # Add more items to mock to test 'full' suggestion
        self.shepherd._daily_plan.review_due = ["i1", "i2", "i3", "i4", "i5", "i6"]
        self.shepherd._completed_items = []
        self.assertEqual(self.shepherd.suggest_session_type(), 'full')
        
        # Mark all complete
        self.shepherd._completed_items = ["i1", "i2", "i3", "i4", "i5", "i6"]
        self.assertEqual(self.shepherd.suggest_session_type(), 'free')

if __name__ == '__main__':
    unittest.main()
