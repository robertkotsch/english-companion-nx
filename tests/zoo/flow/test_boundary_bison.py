"""Unit tests for BoundaryBison agent."""

import pytest
import time
from src.zoo.flow.boundary_bison import BoundaryBison, MODE_OFF, MODE_SOFT, MODE_NORMAL

@pytest.fixture
def bison():
    return BoundaryBison()

def test_mode_switching(bison):
    assert bison.get_mode() == MODE_NORMAL
    bison.set_mode(MODE_OFF)
    assert bison.get_mode() == MODE_OFF
    bison.set_mode("invalid")
    assert bison.get_mode() == MODE_OFF # Should not change

def test_rate_limiting_normal(bison):
    bison.set_mode(MODE_NORMAL) # 1 min limit
    
    # First drill allowed (last_drill_time is 0)
    assert bison.can_drill_now() is True
    
    # Record drill
    bison.record_drill()
    
    # Immediate next drill denied
    assert bison.can_drill_now() is False
    
    # Mock time passing (61s)
    bison.last_drill_time -= 61
    assert bison.can_drill_now() is True

def test_rate_limiting_off(bison):
    bison.set_mode(MODE_OFF)
    assert bison.can_drill_now() is False
