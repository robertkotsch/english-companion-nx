import unittest
from unittest.mock import MagicMock, patch
import sys
import os
from pathlib import Path

# Mock audio dependencies BEFORE importing project modules
sys.modules["soundfile"] = MagicMock()
sys.modules["pyaudio"] = MagicMock()
sys.modules["TTS"] = MagicMock()
sys.modules["TTS.api"] = MagicMock()
sys.modules["notion_client"] = MagicMock()
sys.modules["notion_client.errors"] = MagicMock()

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from voice_assistant_zoo import VoiceAssistantZoo
from src.zoo.flow.day_dolphin import DayState, SessionType

class TestZooFullWiring(unittest.TestCase):
    """Verify that all Phase 1 agents are wired up correctly in the main class."""

    @patch('voice_assistant_zoo.WakeWordDetector')
    @patch('voice_assistant_zoo.AudioRecorder')
    @patch('voice_assistant_zoo.AudioPlayer')
    @patch('voice_assistant_zoo.TranscriptionService')
    @patch('voice_assistant_zoo.SynthesisService')
    @patch('voice_assistant_zoo.OllamaClient')
    @patch('voice_assistant_zoo.NotionNightingale') # Mock Notion to avoid network calls
    def test_initialization_wiring(self, MockNotion, MockOllama, MockSynth, MockTrans, MockPlayer, MockRecorder, MockWake):
        """Test that all agents are initialized."""
        
        assistant = VoiceAssistantZoo(audio_device_index=0)
        
        # Check Flow Agents
        self.assertIsNotNone(assistant.day_dolphin)
        self.assertIsNotNone(assistant.boundary_bison)
        self.assertIsNotNone(assistant.scribe_sparrow)
        
        # Check Memory Agents (The new ones)
        self.assertIsNotNone(assistant.notion_nightingale)
        self.assertIsNotNone(assistant.spaced_squirrel)
        self.assertIsNotNone(assistant.persona_panda)
        
        # Check Planning Agents (The new ones)
        self.assertIsNotNone(assistant.session_shepherd)
        self.assertIsNotNone(assistant.focus_falcon)
        
        # Check Brains
        self.assertIsNotNone(assistant.orchestrator)
        self.assertIsNotNone(assistant.task_tiger)
        self.assertIsNotNone(assistant.coach)
        
        # Check Listeners
        self.assertEqual(len(assistant.listeners), 4)

    @patch('voice_assistant_zoo.WakeWordDetector')
    @patch('voice_assistant_zoo.AudioRecorder')
    @patch('voice_assistant_zoo.AudioPlayer')
    @patch('voice_assistant_zoo.TranscriptionService')
    @patch('voice_assistant_zoo.SynthesisService')
    @patch('voice_assistant_zoo.OllamaClient')
    @patch('voice_assistant_zoo.NotionNightingale')
    def test_boot_sequence(self, MockNotion, MockOllama, MockSynth, MockTrans, MockPlayer, MockRecorder, MockWake):
        """Test that boot sequence calls sync and build_plan."""
        
        # Setup Mocks
        mock_notion_instance = MockNotion.return_value
        
        assistant = VoiceAssistantZoo()
        
        # Mock SessionShepherd to verify calls
        assistant.session_shepherd = MagicMock()
        assistant.session_shepherd.build_daily_plan.return_value = {"focus": "grammar"}
        
        # Mock Wake Detector to exit immediately (raise KeyboardInterrupt or similar to break loop)
        # But run() catches KeyboardInterrupt. So we can just make detect_once raise it.
        assistant.wake_detector.detect_once.side_effect = KeyboardInterrupt("Stop test")
        
        # Run
        assistant.run()
        
        # Verify Notion Sync called
        mock_notion_instance.sync.assert_called_once()
        
        # Verify Plan Built
        assistant.session_shepherd.build_daily_plan.assert_called_once()

    @patch('voice_assistant_zoo.WakeWordDetector')
    @patch('voice_assistant_zoo.AudioRecorder')
    @patch('voice_assistant_zoo.AudioPlayer')
    @patch('voice_assistant_zoo.TranscriptionService')
    @patch('voice_assistant_zoo.SynthesisService')
    @patch('voice_assistant_zoo.OllamaClient')
    @patch('voice_assistant_zoo.NotionNightingale')
    def test_session_flow_wiring(self, MockNotion, MockOllama, MockSynth, MockTrans, MockPlayer, MockRecorder, MockWake):
        """Test that session start/end calls the right agents."""
        
        assistant = VoiceAssistantZoo()
        
        # Mock internal components to track calls
        assistant.day_dolphin = MagicMock()
        assistant.focus_falcon = MagicMock()
        assistant.focus_falcon.select_focus.return_value = "vocab"
        assistant.orchestrator = MagicMock()
        assistant.scribe_sparrow = MagicMock()
        assistant.coach = MagicMock()
        assistant.coach.converse.return_value = "Hello"
        
        # Mock run_session to exit immediately (or we can let it run one loop)
        # Let's mock run_session to just return, since we are testing the surrounding logic in run()
        # But wait, the logic is inside run().
        
        # We need to test the logic inside run() that happens when WakeWordType.START is returned.
        # We can't easily mock the *method* run_session if we are calling run(), unless we patch the class method or replace instance method.
        assistant.run_session = MagicMock()
        
        # Setup Wake Detector to return START once, then raise KeyboardInterrupt
        from src.audio.wake_word import WakeWordType
        assistant.wake_detector.detect_once.side_effect = [WakeWordType.START, KeyboardInterrupt("Stop")]
        
        # Run
        assistant.run()
        
        # Verify Session Start
        assistant.day_dolphin.start_session.assert_called_with(SessionType.QUICK)
        
        # Verify Focus Selection
        assistant.focus_falcon.select_focus.assert_called_once()
        self.assertEqual(assistant.orchestrator.current_focus, "vocab")
        
        # Verify Session Run
        assistant.run_session.assert_called_once()
        
        # Verify Session End
        assistant.day_dolphin.end_session.assert_called_once()
        
        # Verify Summary Generation
        assistant.scribe_sparrow.generate_session_summary.assert_called_once()

if __name__ == '__main__':
    unittest.main()
