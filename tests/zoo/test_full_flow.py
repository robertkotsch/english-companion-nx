"""Integration test for full session flow."""

import pytest
import time
import shutil
import os
from src.zoo.flow.scribe_sparrow import ScribeSparrow
from src.zoo.flow.boundary_bison import BoundaryBison

TEST_DATA_DIR = "tests/temp_flow_data"

def test_full_session_flow():
    # 1. Setup
    if os.path.exists(TEST_DATA_DIR):
        shutil.rmtree(TEST_DATA_DIR)
        
    sparrow = ScribeSparrow(data_dir=TEST_DATA_DIR)
    bison = BoundaryBison()
    
    # 2. Start Session
    session_id = "integration_test_session"
    start_time = time.time()
    utterances = []
    
    # 3. Simulate Conversation
    # Utterance 1: Drill triggered
    if bison.can_drill_now():
        bison.record_drill()
        utterance = {
            "text": "I um go",
            "signals": [{"type": "filler_detected", "data": {"count": 1}}],
            "action": {"type": "drill", "completed": True}
        }
    else:
        utterance = {"text": "I um go", "action": {"type": "ignore"}}
        
    sparrow.log_utterance(utterance)
    utterances.append(utterance)
    
    # Utterance 2: Drill blocked by rate limit
    assert bison.can_drill_now() is False
    utterance2 = {
        "text": "Another one",
        "signals": [],
        "action": {"type": "pass_through"}
    }
    sparrow.log_utterance(utterance2)
    utterances.append(utterance2)
    
    # 4. End Session
    end_time = time.time() + 60 # Mock 1 min duration
    summary = sparrow.generate_session_summary(
        session_id, utterances, start_time, end_time, "fillers", "quick"
    )
    filepath = sparrow.save_session_summary(summary)
    
    # 5. Verify Artifacts
    assert os.path.exists(sparrow.utterance_log_path)
    assert os.path.exists(filepath)
    
    with open(filepath, "r") as f:
        import json
        saved = json.load(f)
        assert saved["stats"]["total_utterances"] == 2
        assert saved["drills"]["offered"] == 1
