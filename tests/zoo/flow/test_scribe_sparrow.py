"""Unit tests for ScribeSparrow agent."""

import pytest
import os
import json
import time
import shutil
from src.zoo.flow.scribe_sparrow import ScribeSparrow

TEST_DATA_DIR = "tests/temp_data"

@pytest.fixture
def sparrow():
    if os.path.exists(TEST_DATA_DIR):
        shutil.rmtree(TEST_DATA_DIR)
    return ScribeSparrow(data_dir=TEST_DATA_DIR)

def test_log_utterance(sparrow):
    data = {"text": "Hello world", "signals": []}
    sparrow.log_utterance(data)
    
    assert os.path.exists(sparrow.utterance_log_path)
    
    with open(sparrow.utterance_log_path, "r") as f:
        line = f.readline()
        record = json.loads(line)
        assert record["text"] == "Hello world"
        assert "timestamp" in record

def test_generate_session_summary(sparrow):
    utterances = [
        {
            "text": "I um like it",
            "signals": [{"type": "filler_detected", "data": {"count": 1}}],
            "action": {"type": "drill", "completed": True}
        },
        {
            "text": "It is good",
            "signals": []
        }
    ]
    
    start = time.time() - 60 # 1 min ago
    end = time.time()
    
    summary = sparrow.generate_session_summary(
        "sess_1", utterances, start, end, "fillers", "quick"
    )
    
    assert summary["session_id"] == "sess_1"
    assert summary["duration_min"] == 1.0
    assert summary["stats"]["total_utterances"] == 2
    assert summary["stats"]["fillers_detected"] == 1
    assert summary["drills"]["completed"] == 1
    assert summary["drills"]["completion_rate"] == 1.0

def test_save_session_summary(sparrow):
    summary = {"session_id": "sess_test", "stats": {}}
    filepath = sparrow.save_session_summary(summary)
    
    assert os.path.exists(filepath)
    with open(filepath, "r") as f:
        saved = json.load(f)
        assert saved["session_id"] == "sess_test"
