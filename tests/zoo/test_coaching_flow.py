"""Integration tests for the full coaching flow."""

import pytest
from zoo.coaching.task_tiger import TaskTiger, DRILL_TYPE_FILLER
from zoo.coaching.coach_coyote import CoachCoyote
from zoo.signals import create_filler_signal

def test_coaching_pipeline():
    # 1. Setup Agents
    tiger = TaskTiger()
    coach = CoachCoyote() # Mock mode
    
    # 2. Simulate Signal
    signal = create_filler_signal("FillerFalcon", "like", 3, 4, 15.0)
    
    # 3. Tiger designs drill
    drill = tiger.design_drill(signal)
    assert drill is not None
    assert drill.type == DRILL_TYPE_FILLER
    assert "like" in drill.instruction
    
    # 4. Coach delivers drill
    context = [{"role": "user", "content": "I like went to the store"}]
    response = coach.deliver_drill(drill, "I like went to the store", context)
    
    # 5. Verify response contains drill instruction
    assert "[MOCK COACH]" in response
    assert drill.instruction in response
    
    # 6. User attempts drill
    user_attempt = "I went to the store"
    success = tiger.validate_attempt(drill, user_attempt)
    assert success is True
