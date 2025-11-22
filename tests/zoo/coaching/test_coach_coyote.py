"""Unit tests for CoachCoyote agent."""

import pytest
from src.zoo.coaching.coach_coyote import CoachCoyote
from src.zoo.coaching.task_tiger import Drill, DRILL_TYPE_FILLER

@pytest.fixture
def coach():
    return CoachCoyote() # No LLM client = Mock mode

def test_converse_mock(coach):
    context = [{"role": "user", "content": "Hello"}]
    response = coach.converse("Hello", context)
    assert "[MOCK COACH]" in response

def test_deliver_drill_mock(coach):
    drill = Drill(
        type=DRILL_TYPE_FILLER,
        instruction="Say it without um",
        target_content="um",
        expected_response_type="reformulate"
    )
    context = [{"role": "user", "content": "I um like it"}]
    
    response = coach.deliver_drill(drill, "I um like it", context)
    assert "[MOCK COACH]" in response
    assert "Say it without um" in response

def test_prompt_construction(coach):
    # Access private method for testing
    context = [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello"}]
    history = coach._format_history(context)
    assert "User: Hi" in history
    assert "Coach: Hello" in history
