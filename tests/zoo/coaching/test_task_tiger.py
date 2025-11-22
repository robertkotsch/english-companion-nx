"""Unit tests for TaskTiger agent."""

import pytest
from zoo.coaching.task_tiger import (
    TaskTiger, 
    Drill, 
    DRILL_TYPE_FILLER, 
    DRILL_TYPE_GRAMMAR, 
    DRILL_TYPE_VOCAB,
    FILLER_VARIANT_STANDARD,
    FILLER_VARIANT_PAUSE,
    FILLER_VARIANT_BREATH
)
from zoo.signals import (
    create_filler_signal,
    create_grammar_signal,
    create_vocab_signal,
    SIGNAL_VOCAB_OPPORTUNITY
)

@pytest.fixture
def tiger():
    return TaskTiger()

def test_design_filler_drill(tiger):
    signal = create_filler_signal("FillerFalcon", "um", 2, 5, 12.0)
    drill = tiger.design_drill(signal)
    
    assert drill is not None
    assert drill.type == DRILL_TYPE_FILLER
    assert drill.target_content == "um"
    assert drill.variant in [FILLER_VARIANT_STANDARD, FILLER_VARIANT_PAUSE, FILLER_VARIANT_BREATH]
    
    # Test validation
    assert tiger.validate_attempt(drill, "I think we should go") == True
    assert tiger.validate_attempt(drill, "I think um we should go") == False

def test_design_grammar_drill_with_suggestion(tiger):
    signal = create_grammar_signal(
        "GrammarGiraffe", 
        "tense", 
        0.8, 
        "I goed to the store", 
        "I went to the store"
    )
    drill = tiger.design_drill(signal)
    
    assert drill is not None
    assert drill.type == DRILL_TYPE_GRAMMAR
    assert drill.target_content == "I went to the store"
    assert drill.expected_response_type == "repeat"
    
    # Test validation (fuzzy matching)
    assert tiger.validate_attempt(drill, "I went to the store") == True
    assert tiger.validate_attempt(drill, "Yes, I went to the store") == True # Substring match
    assert tiger.validate_attempt(drill, "I goed there") == False

def test_design_grammar_drill_no_suggestion(tiger):
    signal = create_grammar_signal(
        "GrammarGiraffe", 
        "tense", 
        0.8, 
        "I goed to the store"
    )
    # Manually remove suggestion for this test case
    signal.data["suggestion"] = ""
    
    drill = tiger.design_drill(signal)
    
    assert drill is not None
    assert drill.type == DRILL_TYPE_GRAMMAR
    assert drill.target_content == "I goed to the store"
    assert drill.expected_response_type == "reformulate"
    
    # Validation for reformulation is always True in MVP
    assert tiger.validate_attempt(drill, "Anything") == True

def test_design_vocab_drill(tiger):
    signal = create_vocab_signal(
        "LexiLynx",
        SIGNAL_VOCAB_OPPORTUNITY,
        "leverage",
        0.7,
        definition="use strategically"
    )
    drill = tiger.design_drill(signal)
    
    assert drill is not None
    assert drill.type == DRILL_TYPE_VOCAB
    assert drill.target_content == "leverage"
    
    # Test validation
    assert tiger.validate_attempt(drill, "We should leverage our assets") == True
    assert tiger.validate_attempt(drill, "We should use our assets") == False
