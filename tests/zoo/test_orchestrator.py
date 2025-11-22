import pytest
import time
from zoo.orchestrator import OrchestratorOctopus, ActionType
from zoo.signals import Signal, SIGNAL_GRAMMAR_ERROR, SIGNAL_FILLER_DETECTED, SIGNAL_VOCAB_OPPORTUNITY

class TestOrchestratorOctopus:
    
    @pytest.fixture
    def orchestrator(self):
        return OrchestratorOctopus(config={
            "drill_cooldown_sec": 0.0, # Disable cooldown for easier testing
            "max_drills_per_session": 100
        })

    def test_initialization(self, orchestrator):
        assert orchestrator.drills_this_session == 0
        assert orchestrator.last_drill_time == 0.0
        assert orchestrator.coach_intensity == "normal"

    def test_score_signal_basic(self, orchestrator):
        # Severity 0.5 -> Base score 2.5
        signal = Signal(
            source="Test", type="test", severity=0.5, scope="utterance", 
            realtime_desirable=False, data={}
        )
        score = orchestrator._score_signal(signal)
        assert score == 2.5

    def test_score_signal_realtime_boost(self, orchestrator):
        # Severity 0.5 -> Base 2.5 + Realtime 2.0 = 4.5
        signal = Signal(
            source="Test", type="test", severity=0.5, scope="utterance", 
            realtime_desirable=True, data={}
        )
        score = orchestrator._score_signal(signal)
        assert score == 4.5

    def test_score_signal_focus_boost(self, orchestrator):
        orchestrator.current_focus = "grammar"
        # Severity 0.5 -> Base 2.5 * 1.5 (Focus) = 3.75
        signal = Signal(
            source="Test", type=SIGNAL_GRAMMAR_ERROR, severity=0.5, scope="utterance", 
            realtime_desirable=False, data={}
        )
        score = orchestrator._score_signal(signal)
        assert score == 3.75

    def test_decide_action_drill_now(self, orchestrator):
        # Score 7.0 (> 6.0 threshold) -> DRILL_NOW
        signal = Signal(
            source="Test", type="test", severity=1.0, scope="utterance", 
            realtime_desirable=True, data={}
        )
        # 1.0 * 5.0 + 2.0 = 7.0
        score = orchestrator._score_signal(signal)
        action = orchestrator._decide_action(signal, score)
        assert action.type == ActionType.DRILL_NOW

    def test_decide_action_buffer(self, orchestrator):
        # Score 3.0 (2.0 <= x < 6.0) -> BUFFER
        signal = Signal(
            source="Test", type="test", severity=0.6, scope="utterance", 
            realtime_desirable=False, data={}
        )
        # 0.6 * 5.0 = 3.0
        score = orchestrator._score_signal(signal)
        action = orchestrator._decide_action(signal, score)
        assert action.type == ActionType.BUFFER

    def test_decide_action_ignore(self, orchestrator):
        # Score 1.0 (< 2.0) -> IGNORE
        signal = Signal(
            source="Test", type="test", severity=0.2, scope="utterance", 
            realtime_desirable=False, data={}
        )
        # 0.2 * 5.0 = 1.0
        score = orchestrator._score_signal(signal)
        action = orchestrator._decide_action(signal, score)
        assert action.type == ActionType.IGNORE

    def test_cooldown_logic(self):
        orchestrator = OrchestratorOctopus(config={"drill_cooldown_sec": 60.0})
        
        # First drill
        signal = Signal(source="Test", type="test", severity=1.0, scope="utterance", realtime_desirable=True, data={})
        action = orchestrator.process_utterance("test", [signal])
        assert action.type == ActionType.DRILL_NOW
        
        # Immediate second drill -> Should BUFFER due to cooldown
        action = orchestrator.process_utterance("test", [signal])
        assert action.type == ActionType.BUFFER
        assert "Drill cooldown" in action.reason

    def test_max_drills_limit(self):
        orchestrator = OrchestratorOctopus(config={"max_drills_per_session": 1, "drill_cooldown_sec": 0})
        
        signal = Signal(source="Test", type="test", severity=1.0, scope="utterance", realtime_desirable=True, data={})
        
        # 1st drill -> OK
        action = orchestrator.process_utterance("test", [signal])
        assert action.type == ActionType.DRILL_NOW
        
        # 2nd drill -> BUFFER due to limit
        action = orchestrator.process_utterance("test", [signal])
        assert action.type == ActionType.BUFFER
        assert "Max drills reached" in action.reason

    def test_coach_intensity_off(self):
        orchestrator = OrchestratorOctopus(config={"coach_intensity": "off"})
        signal = Signal(source="Test", type="test", severity=1.0, scope="utterance", realtime_desirable=True, data={})
        
        action = orchestrator.process_utterance("test", [signal])
        assert action.type == ActionType.BUFFER
        assert "Coach mode is off" in action.reason

    def test_process_utterance_no_signals(self, orchestrator):
        action = orchestrator.process_utterance("hello", [])
        assert action.type == ActionType.PASS_THROUGH

    def test_process_utterance_prioritization(self, orchestrator):
        # Create two signals: one high priority, one low
        high_sig = Signal(source="High", type="high", severity=1.0, scope="utterance", realtime_desirable=True, data={}) # Score 7.0
        low_sig = Signal(source="Low", type="low", severity=0.2, scope="utterance", realtime_desirable=False, data={}) # Score 1.0
        
        action = orchestrator.process_utterance("test", [low_sig, high_sig])
        
        assert action.type == ActionType.DRILL_NOW
        assert action.signal == high_sig
