#!/usr/bin/env python3
"""
English Companion NX - Voice Assistant (Phase 2B)
Always-on voice assistant with wake word detection

Flow:
1. 👂 Wake word detection (always listening)
2. 🎯 "Hey Jarvis" detected → beep
3. 🎤 Record user speech (5 seconds)
4. 🧠 Whisper transcription
5. 💬 Ollama LLM response
6. 🔊 TTS synthesis
7. 🔁 Return to wake word listening

Usage:
    python voice_assistant.py

Say "hey jarvis" to start a conversation.
Press Ctrl+C to exit.
"""

import time
import torch
from pathlib import Path

from src.core.config import Config
from src.core.memory import MemoryMonitor
from src.conversation.manager import ConversationManager
from src.conversation.logger import ConversationLogger
from src.audio.recorder import AudioRecorder
from src.audio.player import AudioPlayer
from src.audio.wake_word import WakeWordDetector, WakeWordType
from src.speech.transcription import TranscriptionService
from src.speech.synthesis import SynthesisService


class VoiceAssistant:
    """Always-on voice assistant with wake word detection"""

    def __init__(
        self,
        wake_word_model: str = "hey_jarvis",
        wake_word_threshold: float = 0.5,
        audio_device_index: int = 0
    ):
        """
        Initialize voice assistant

        Args:
            wake_word_model: Wake word model name (default: "hey_jarvis")
            wake_word_threshold: Detection threshold 0.0-1.0 (default: 0.5)
            audio_device_index: PyAudio device index (default: 0 for PowerConf S3)
        """
        print("🚀 English Companion NX - Voice Assistant (Phase 2B)")
        print("=" * 60)

        # Check GPU availability
        device = "cuda" if torch.cuda.is_available() and Config.USE_GPU else "cpu"
        print(f"🖥️  Device: {device.upper()}")
        if device == "cuda":
            print(f"   GPU: {torch.cuda.get_device_name(0)}")

        # Initialize wake word detector
        print("\n👂 Initializing wake word detection...")
        self.wake_detector = WakeWordDetector(
            start_model=wake_word_model,
            start_threshold=wake_word_threshold,
            audio_device_index=audio_device_index
        )

        # Initialize audio components (separate from wake word detection)
        print("\n🎤 Initializing audio system...")
        self.recorder = AudioRecorder()
        self.recorder.cleanup_previous_instances()
        self.player = AudioPlayer()

        # Load AI models
        print("\n📦 Loading AI models...")
        self.transcription = TranscriptionService()
        self.synthesis = SynthesisService()

        # Initialize conversation system
        print("\n💬 Initializing conversation system...")
        self.conversation = ConversationManager()
        self.logger = ConversationLogger()

        # Initialize memory monitoring
        print("\n🧠 Initializing memory monitoring...")
        self.memory_monitor = MemoryMonitor(
            warning_threshold=0.85,
            critical_threshold=0.95,
            cleanup_interval=10  # Cleanup every 10 conversations
        )

        print("\n✅ All systems ready!")
        print("=" * 60)
        print(f"💾 {self.memory_monitor.get_memory_summary()}")

    def handle_conversation(self):
        """
        Handle one conversation turn after wake word detection

        Returns:
            bool: True if successful, False if error
        """
        try:
            start_time = time.time()

            # 1. Record audio with Voice Activity Detection (VAD)
            # Stops automatically when user stops speaking
            audio_file = self.recorder.record_with_vad(
                silence_threshold=0.01,   # Audio level below this = silence
                silence_duration=1.5,     # Stop after 1.5s of silence
                min_duration=0.5,         # Minimum 0.5s recording
                max_duration=30.0         # Maximum 30s (safety limit)
            )

            # 2. Transcribe with Whisper
            print("🧠 Transcribing...")
            user_message = self.transcription.transcribe(audio_file)
            self.recorder.cleanup_file(audio_file)

            if not user_message:
                print("⚠️  No speech detected. Say 'hey jarvis' to try again.\n")
                return False

            print(f"👤 You: {user_message}")

            # 3. Generate LLM response
            print("💭 Thinking...")
            llm_start = time.time()
            response = self.conversation.generate_response(user_message)
            llm_time = time.time() - llm_start
            print(f"✅ Response generated ({llm_time:.2f}s)")

            # 4. Synthesize speech
            print("🔊 Synthesizing speech...")
            tts_file = self.synthesis.synthesize(response)

            # 5. Play response
            print(f"🤖 Assistant: {response}\n")
            self.player.play(tts_file)
            self.synthesis.cleanup_file(tts_file)

            # 6. Log conversation
            total_time = time.time() - start_time
            self.logger.log_exchange(
                user_message=user_message,
                assistant_message=response,
                metadata={
                    "response_time_ms": int(total_time * 1000),
                    "llm_time_ms": int(llm_time * 1000),
                    "trigger": "wake_word"
                }
            )

            # 7. Memory monitoring and cleanup
            self.memory_monitor.on_conversation_complete()

            # Show stats
            print(f"📊 {self.conversation.get_context_summary()}")
            print(f"💾 {self.memory_monitor.get_memory_summary()}")
            print(f"⏱️  Total: {total_time:.2f}s")

            return True

        except Exception as e:
            print(f"\n❌ Error during conversation: {e}")
            import traceback
            traceback.print_exc()
            return False

    def run(self):
        """
        Run always-on voice assistant

        Main loop:
        1. Listen for wake word
        2. When detected, handle conversation
        3. Return to listening
        """
        print("\n" + "=" * 60)
        print("👂 ALWAYS-ON VOICE ASSISTANT")
        print("=" * 60)
        print(f"Wake word: 'hey jarvis'")
        print("Say the wake word to start a conversation")
        print("Press Ctrl+C to exit")
        print("=" * 60)
        print()

        conversation_count = 0

        try:
            # Start wake word detector
            self.wake_detector.start()

            print("🎧 Listening for wake word...\n")

            while True:
                # Listen for wake word (blocking)
                result = self.wake_detector.detect_once(timeout=None)

                if result == WakeWordType.START:
                    print(f"\n{'='*60}")
                    print(f"🎯 WAKE WORD DETECTED! (Conversation #{conversation_count + 1})")
                    print(f"{'='*60}\n")

                    # Temporarily stop wake word detection during conversation
                    self.wake_detector.stop()

                    # Handle the conversation
                    success = self.handle_conversation()

                    if success:
                        conversation_count += 1

                    # Restart wake word detection
                    print(f"\n{'='*60}")
                    print("🎧 Returning to wake word listening...")
                    print(f"{'='*60}\n")
                    self.wake_detector.start()

        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")
        except Exception as e:
            print(f"\n❌ Fatal error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Cleanup
            print("\n🛑 Shutting down...")
            self.wake_detector.stop()

            # Show final statistics
            print("\n📊 Final Statistics")
            print("=" * 60)
            print(f"Total conversations: {conversation_count}")
            stats = self.wake_detector.get_stats()
            print(f"Wake word detections: {stats['start_detections']}")
            print("=" * 60)

            # Memory statistics
            print("\n📊 Final Memory Statistics")
            self.memory_monitor.log_memory_stats()

            # Flush logs
            print("\n🔄 Flushing conversation logs...")
            self.logger.cleanup()

            # Final cleanup
            print("🧹 Final memory cleanup...")
            self.memory_monitor.cleanup(force=True)

            print("\n✅ Shutdown complete. Goodbye! 👋\n")


def main():
    """Main entry point"""
    import sys

    # Parse command line arguments
    wake_word_model = "hey_jarvis"
    threshold = 0.5
    device_index = 0

    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h"]:
        print("Usage: python voice_assistant.py [MODEL] [THRESHOLD] [DEVICE]")
        print()
        print("Arguments:")
        print("  MODEL      - Wake word model (default: hey_jarvis)")
        print("  THRESHOLD  - Detection threshold 0.0-1.0 (default: 0.5)")
        print("  DEVICE     - Audio device index (default: 0)")
        print()
        print("Examples:")
        print("  python voice_assistant.py")
        print("  python voice_assistant.py hey_jarvis 0.5 0")
        print("  python voice_assistant.py alexa 0.6 0")
        return

    if len(sys.argv) > 1:
        wake_word_model = sys.argv[1]
    if len(sys.argv) > 2:
        threshold = float(sys.argv[2])
    if len(sys.argv) > 3:
        device_index = int(sys.argv[3])

    try:
        assistant = VoiceAssistant(
            wake_word_model=wake_word_model,
            wake_word_threshold=threshold,
            audio_device_index=device_index
        )
        assistant.run()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
