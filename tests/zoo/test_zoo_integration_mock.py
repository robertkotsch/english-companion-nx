import unittest
from unittest.mock import MagicMock, patch
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Mock hardware dependencies BEFORE importing voice_assistant_zoo
sys.modules['soundfile'] = MagicMock()
sys.modules['pyaudio'] = MagicMock()
sys.modules['pvporcupine'] = MagicMock()
sys.modules['torch'] = MagicMock()
sys.modules['torch.nn'] = MagicMock()
sys.modules['torch.nn.functional'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['whisper'] = MagicMock()
sys.modules['ollama'] = MagicMock()
sys.modules['notion_client'] = MagicMock()
sys.modules['TTS'] = MagicMock()
sys.modules['TTS.api'] = MagicMock()

from voice_assistant_zoo import VoiceAssistantZoo
from src.audio.wake_word import WakeWordType
from src.zoo.orchestrator import Action, ActionType
from src.zoo.signals import Signal, SIGNAL_FILLER_DETECTED

class TestZooIntegrationMock(unittest.TestCase):
    """Mock integration test for VoiceAssistantZoo"""

    @patch('voice_assistant_zoo.WakeWordDetector')
    @patch('voice_assistant_zoo.AudioRecorder')
    @patch('voice_assistant_zoo.AudioPlayer')
    @patch('voice_assistant_zoo.TranscriptionService')
    @patch('voice_assistant_zoo.SynthesisService')
    @patch('voice_assistant_zoo.OllamaClient')
    def test_full_pipeline_flow(self, MockOllama, MockSynth, MockTrans, MockPlayer, MockRecorder, MockWake):
        """Test the full pipeline flow with mocks"""
        
        # Setup Mocks
        mock_wake = MockWake.return_value
        mock_recorder = MockRecorder.return_value
        mock_trans = MockTrans.return_value
        mock_synth = MockSynth.return_value
        mock_ollama = MockOllama.return_value
        
        # 1. Wake Word Sequence: START -> NONE (speak) -> STOP
        # We need to control the loop in run() and run_session()
        # run() calls detect_once() -> START
        # run_session() calls detect_once() -> NONE (triggers handle_conversation) -> STOP
        
        # Sequence for run(): [START, STOP (to break loop? no run() loops forever)]
        # We'll interrupt run() by raising KeyboardInterrupt after one session
        
        # Sequence for run_session(): [NONE, STOP]
        
        # But wait, run() calls run_session().
        # Let's just test handle_conversation() directly first to verify the core logic.
        
        assistant = VoiceAssistantZoo()
        
        # Mock Transcription
        mock_trans.transcribe.return_value = "I think um we should go."
        
        # Mock Zoo Components to verify interactions
        assistant.listeners = [MagicMock()]
        assistant.listeners[0].process_utterance.return_value = [
            Signal(source="MockListener", type=SIGNAL_FILLER_DETECTED, severity=0.8, 
                   scope="utterance", realtime_desirable=True, data={"filler": "um"}, 
                   timestamp=0, utterance_id="test")
        ]
        assistant.listeners[0].name = "MockListener"
        
        assistant.orchestrator = MagicMock()
        assistant.orchestrator.process_utterance.return_value = Action(ActionType.DRILL_NOW, signal=assistant.listeners[0].process_utterance.return_value[0], reason="Test")
        
        assistant.task_tiger = MagicMock()
        assistant.task_tiger.design_drill.return_value = MagicMock(instruction="Drill instruction")
        
        assistant.coach = MagicMock()
        assistant.coach.deliver_drill.return_value = "Coach response with drill"
        
        # Manually set detected_sample_rate (normally set in run())
        assistant.detected_sample_rate = 16000
        
        # Run handle_conversation
        print("\n--- Testing handle_conversation ---")
        success = assistant.handle_conversation()
        
        # Verify
        self.assertTrue(success)
        
        # 1. Recorder called
        mock_recorder.record_with_vad.assert_called_once()
        
        # 2. Transcribe called
        mock_trans.transcribe.assert_called_once()
        
        # 3. Listeners called
        assistant.listeners[0].process_utterance.assert_called_once()
        
        # 4. Orchestrator called
        assistant.orchestrator.process_utterance.assert_called_once()
        
        # 5. TaskTiger called (since Action was DRILL_NOW)
        assistant.task_tiger.design_drill.assert_called_once()
        
        # 6. Coach called
        assistant.coach.deliver_drill.assert_called_once()
        
        # 7. Synthesis called
        mock_synth.synthesize.assert_called_with("Coach response with drill")
        
        print("--- Test Passed ---")

if __name__ == '__main__':
    unittest.main()
