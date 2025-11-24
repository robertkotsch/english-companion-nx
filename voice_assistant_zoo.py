#!/usr/bin/env python3
"""
English Companion NX - Voice Assistant (Zoo Edition)
Phase 1.7 Integration

Flow:
1. 👂 Wake word detection
2. 🎤 Record user speech
3. 🧠 Whisper transcription
4. 🦁 Zoo Pipeline:
   - Listeners analyze text -> Signals
   - Orchestrator prioritizes -> Action
   - TaskTiger designs drill (if needed)
   - CoachCoyote generates response
5. 🔊 TTS synthesis
6. 📝 Logging (ScribeSparrow)
"""

import time
import torch
import logging
from pathlib import Path
from typing import Optional, List

from src.core.config import Config
from src.core.memory import MemoryMonitor
from src.audio.recorder import AudioRecorder
from src.audio.player import AudioPlayer
from src.audio.wake_word import WakeWordDetector, WakeWordType
from src.speech.transcription import TranscriptionService
from src.speech.synthesis import SynthesisService
from src.conversation.llm_client import OllamaClient

# Zoo Components
from src.zoo.orchestrator import OrchestratorOctopus, ActionType
from src.zoo.coaching.coach_coyote import CoachCoyote
from src.zoo.coaching.task_tiger import TaskTiger
from src.zoo.coaching.session_shepherd import SessionShepherd
from src.zoo.coaching.focus_falcon import FocusFalcon
from src.zoo.flow.day_dolphin import DayDolphin, DayState, SessionType
from src.zoo.flow.scribe_sparrow import ScribeSparrow
from src.zoo.flow.boundary_bison import BoundaryBison
from src.zoo.listeners.grammar_giraffe import GrammarGiraffe
from src.zoo.listeners.filler_falcon import FillerFalcon
from src.zoo.listeners.tempo_tiger import TempoTiger
from src.zoo.listeners.lexi_lynx import LexiLynx
from src.zoo.memory.notion_nightingale import NotionNightingale
from src.zoo.memory.spaced_squirrel import SpacedSquirrel
from src.zoo.memory.persona_panda import PersonaPanda

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VoiceAssistantZoo")

class VoiceAssistantZoo:
    """Zoo-enabled voice assistant"""

    def __init__(
        self,
        wake_word_model: str = "hey_jarvis",
        stop_word_model: str = "alexa",
        wake_word_threshold: float = 0.5,
        stop_word_threshold: float = 0.5,
        audio_device_index: Optional[int] = None,
        audio_device_name: Optional[str] = None
    ):
        print("🦁 English Companion NX - Zoo Edition (Phase 1.7)")
        print("=" * 60)

        # Check GPU
        device = "cuda" if torch.cuda.is_available() and Config.USE_GPU else "cpu"
        print(f"🖥️  Device: {device.upper()}")

        # 1. Initialize Hardware & Core Services
        print("\n🎤 Initializing audio system...")
        self.wake_detector = WakeWordDetector(
            start_model=wake_word_model,
            stop_model=stop_word_model,
            start_threshold=wake_word_threshold,
            stop_threshold=stop_word_threshold,
            audio_device_index=audio_device_index,
            audio_device_name=audio_device_name
        )
        self.recorder = AudioRecorder()
        self.recorder.cleanup_previous_instances()
        self.player = AudioPlayer()
        
        self.audio_device_index = audio_device_index
        self.audio_device_name = audio_device_name

        print("\n📦 Loading AI models...")
        self.transcription = TranscriptionService()
        self.synthesis = SynthesisService()
        self.memory_monitor = MemoryMonitor()

        # 2. Initialize Zoo Agents
        print("\n🦁 Initializing Zoo Agents...")
        
        # Flow & State
        self.day_dolphin = DayDolphin(start_hour=0, end_hour=23)
        self.boundary_bison = BoundaryBison()
        self.scribe_sparrow = ScribeSparrow()
        
        # Memory Agents
        print("   - Memory Agents...")
        self.notion_nightingale = NotionNightingale(
            api_key=Config.NOTION_API_KEY,
            database_id=Config.NOTION_DATABASE_ID
        )
        self.spaced_squirrel = SpacedSquirrel()
        self.persona_panda = PersonaPanda()

        # Planning Agents
        print("   - Planning Agents...")
        self.focus_falcon = FocusFalcon()
        self.session_shepherd = SessionShepherd(
            spaced_squirrel=self.spaced_squirrel,
            focus_falcon=self.focus_falcon
        )

        # Brains
        self.orchestrator = OrchestratorOctopus()
        self.task_tiger = TaskTiger()
        
        # Coach (Shared LLM Client)
        self.llm_client = OllamaClient()
        self.coach = CoachCoyote(llm_client=self.llm_client)
        
        # Listeners
        print("   - Listeners...")
        self.listeners = [
            GrammarGiraffe(),
            FillerFalcon(),
            TempoTiger(),
            LexiLynx()
        ]

        # Conversation Context
        self.context = [] 
        self.max_context_size = 20

        print("\n✅ All systems ready!")
        print("=" * 60)

    def handle_conversation(self):
        """Handle one conversation turn"""
        try:
            start_time = time.time()

            # 1. Record
            audio_file = self.recorder.record_with_vad(
                silence_threshold=0.01,
                silence_duration=3.0,
                min_duration=0.5,
                max_duration=30.0,
                sample_rate=self.detected_sample_rate,
                device_index=self.audio_device_index
            )

            # 2. Transcribe
            print("🧠 Transcribing...")
            user_message = self.transcription.transcribe(audio_file)
            self.recorder.cleanup_file(audio_file)

            if not user_message or self._is_whisper_hallucination(user_message):
                if user_message:
                    print(f"⚠️  Detected hallucination: '{user_message}' (ignoring)\n")
                return False

            print(f"👤 You: {user_message}")

            # 3. Zoo Pipeline
            print("🦁 Zoo Processing...")
            
            # A. Listeners
            all_signals = []
            metadata = {
                "timestamp": time.time(),
                "session_id": "current_session" # TODO: Get from DayDolphin
            }
            
            for listener in self.listeners:
                try:
                    signals = listener.process_utterance(user_message, metadata)
                    all_signals.extend(signals)
                except Exception as e:
                    print(f"⚠️  Listener {listener.name} failed: {e}")

            if all_signals:
                print(f"   - Signals: {[s.type for s in all_signals]}")

            # B. Orchestrator
            action = self.orchestrator.process_utterance(user_message, all_signals)
            print(f"   - Action: {action.type.value} ({action.reason})")

            # C. Coach / TaskTiger
            response = ""
            drill = None
            
            if action.type == ActionType.DRILL_NOW and action.signal:
                print("   - Designing Drill...")
                drill = self.task_tiger.design_drill(action.signal)
                if drill:
                    print(f"   - 🐅 TaskTiger: Drill designed ({drill.type})")
                    response = self.coach.deliver_drill(
                        drill=drill,
                        utterance=user_message,
                        context=self.context,
                        focus=self.orchestrator.current_focus,
                        intensity=self.boundary_bison.get_mode()
                    )
                    # Mark drill as completed in SpacedSquirrel
                    # In MVP, we assume if we delivered it, it counts as an "attempt"
                    # In a full system, we'd wait for the user's NEXT response to verify
                    try:
                        self.spaced_squirrel.mark_reviewed(drill.id, success=True)
                        print(f"   - 🐿️  SpacedSquirrel: Marked drill {drill.id} as reviewed")
                    except Exception as e:
                        print(f"   - ⚠️  SpacedSquirrel: Failed to mark drill: {e}")
                else:
                    # Fallback if drill design fails
                    response = self.coach.converse(user_message, self.context)
            else:
                # Normal conversation
                response = self.coach.converse(
                    utterance=user_message,
                    context=self.context,
                    focus=self.orchestrator.current_focus,
                    intensity=self.boundary_bison.get_mode()
                )

            print(f"🤖 Assistant: {response}\n")

            # 4. Synthesize & Play
            print("🔊 Synthesizing...")
            tts_file = self.synthesis.synthesize(response)
            self.player.play(tts_file)
            self.synthesis.cleanup_file(tts_file)

            # 5. Update Context & Log
            self._update_context(user_message, response)
            
            # Log to ScribeSparrow
            self.scribe_sparrow.log_utterance({
                "utterance": user_message,
                "response": response,
                "signals": [s.to_dict() for s in all_signals], # Serialize signals
                "action": str(action.type.value), # Serialize action
                "drill": drill.id if drill else None,
                "duration_ms": int((time.time() - start_time) * 1000)
            })

            # Memory monitoring
            print(f"💾 {self.memory_monitor.get_memory_summary()}")
            self.memory_monitor.on_conversation_complete()

            return True

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _update_context(self, user_msg: str, assistant_msg: str):
        """Update local conversation context"""
        self.context.append({"role": "user", "content": user_msg})
        self.context.append({"role": "assistant", "content": assistant_msg})
        
        # Prune
        if len(self.context) > self.max_context_size:
            self.context = self.context[-self.max_context_size:]

    def _is_whisper_hallucination(self, text: str) -> bool:
        """Check for Whisper hallucinations"""
        normalized = text.lower().strip().strip('.,!?;:')
        hallucinations = {
            'you', 'thank you', 'thanks', 'okay', 'ok', 'yeah', 'yes', 'no', 
            'um', 'uh', 'hmm', 'ah', ''
        }
        if len(normalized) <= 2: return True
        return normalized in hallucinations

    def run(self):
        """Main loop"""
        print("\n" + "=" * 60)
        print("👂 LISTENING FOR WAKE WORD ('hey jarvis')")
        print("=" * 60)

        # Boot the day
        print("\n🌅 DayDolphin: Booting day...")
        self.day_dolphin.boot()
        
        # Sync Notion
        print("🐦 NotionNightingale: Syncing vocabulary...")
        try:
            self.notion_nightingale.sync()
            print("   - Sync complete.")
        except Exception as e:
            print(f"   - Sync failed (continuing with cache): {e}")

        # Load User Profile
        print("🐼 PersonaPanda: Loading user profile...")
        user_profile = self.persona_panda.get_profile()
        print(f"   - Goals: {user_profile.cefr_target} level, Focus: {user_profile.weekly_focus}")
        print(f"   - Intensity: {user_profile.coach_intensity}, Topics: {', '.join(user_profile.topics[:3])}")

        # Build Plan
        print("🐑 SessionShepherd: Building daily plan...")
        daily_plan = self.session_shepherd.build_daily_plan()
        print(f"   - Plan built: Focus={daily_plan.get('focus', 'general')}")

        try:
            self.wake_detector.start()
            self.audio_device_index = self.wake_detector.audio_device_index
            self.detected_sample_rate = self.wake_detector.device_sample_rate
            
            while True:
                result = self.wake_detector.detect_once(timeout=None)
                
                if result == WakeWordType.START:
                    print("\n🎯 WAKE WORD DETECTED!")
                    
                    # Start Session
                    session_type = SessionType.QUICK # Default
                    print(f"🐬 DayDolphin: Starting {session_type.value} session")
                    self.day_dolphin.start_session(session_type)
                    
                    # Select Focus
                    focus = self.focus_falcon.select_focus(recent_stats={})
                    self.orchestrator.current_focus = focus
                    print(f"🦅 FocusFalcon: Selected session focus -> '{focus}'")
                    
                    self.run_session()
                    
                    # End Session
                    print("🐬 DayDolphin: Ending session")
                    self.day_dolphin.end_session()
                    
                    # Summary
                    summary = self.scribe_sparrow.generate_session_summary()
                    print(f"📝 ScribeSparrow: Session summary generated ({summary.get('duration_min', 0):.1f} min)")
                    
                    print("\n👂 Returning to wake word listening...")

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
        finally:
            self.wake_detector.stop()
            self.day_dolphin.shutdown()

    def run_session(self, idle_timeout: float = 30.0):
        """Run a conversation session"""
        last_activity = time.time()
        
        # Greet
        greeting = self.coach.converse("Hello", [], focus=self.orchestrator.current_focus) 
        print(f"🤖 Assistant: {greeting}\n")
        tts_file = self.synthesis.synthesize(greeting)
        self.player.play(tts_file)
        self.synthesis.cleanup_file(tts_file)
        self._update_context("Hello", greeting)

        while True:
            print("\n👂 Listening...")
            result = self.wake_detector.detect_once(timeout=2.0)

            if result == WakeWordType.STOP:
                print("🛑 STOP WORD DETECTED")
                break

            elif result == WakeWordType.START:
                # User said wake word again during session - just acknowledge
                print("ℹ️  Already in session - continue speaking!")
                last_activity = time.time()
                continue

            elif result == WakeWordType.NONE:
                # No wake word detected in 2s - check if idle or user wants to speak
                idle_duration = time.time() - last_activity

                if idle_duration >= idle_timeout:
                    # Idle timeout reached - end session
                    print("💤 IDLE TIMEOUT")
                    break
                else:
                    # Assume user wants to speak
                    # Stop wake detector to free audio
                    self.wake_detector.stop()

                    success = self.handle_conversation()

                    self.wake_detector.start()

                    if success:
                        last_activity = time.time()

def main():
    import sys

    # Parse command line arguments
    wake_word_model = "hey_jarvis"
    stop_word_model = "alexa"
    wake_threshold = 0.5
    stop_threshold = 0.5
    device_index = None
    device_name = Config.AUDIO_DEVICE_NAME if hasattr(Config, 'AUDIO_DEVICE_NAME') else None

    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h"]:
        print("Usage: python voice_assistant_zoo.py [WAKE_MODEL] [STOP_MODEL] [WAKE_THRESH] [STOP_THRESH] [DEVICE]")
        print()
        print("Arguments:")
        print("  WAKE_MODEL  - Wake word model (default: hey_jarvis)")
        print("  STOP_MODEL  - Stop word model (default: alexa)")
        print("  WAKE_THRESH - Wake detection threshold 0.0-1.0 (default: 0.5)")
        print("  STOP_THRESH - Stop detection threshold 0.0-1.0 (default: 0.5)")
        print("  DEVICE      - Audio device index or name pattern (default: from .env or auto-detect)")
        print()
        print("Available models: hey_jarvis, alexa, hey_mycroft, timer")
        return

    if len(sys.argv) > 1:
        wake_word_model = sys.argv[1]
    if len(sys.argv) > 2:
        stop_word_model = sys.argv[2]
    if len(sys.argv) > 3:
        wake_threshold = float(sys.argv[3])
    if len(sys.argv) > 4:
        stop_threshold = float(sys.argv[4])
    if len(sys.argv) > 5:
        # Try to parse as integer (device index), otherwise treat as device name
        try:
            device_index = int(sys.argv[5])
            device_name = None
        except ValueError:
            device_name = sys.argv[5]
            device_index = None

    try:
        assistant = VoiceAssistantZoo(
            wake_word_model=wake_word_model,
            stop_word_model=stop_word_model,
            wake_word_threshold=wake_threshold,
            stop_word_threshold=stop_threshold,
            audio_device_index=device_index,
            audio_device_name=device_name
        )
        assistant.run()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"Fatal Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
