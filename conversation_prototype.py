#!/usr/bin/env python3
"""
English Companion NX - Conversation Prototype
Simple conversational flow: Record → Transcribe → LLM → TTS → Play

Usage:
    python conversation_prototype.py

Press Enter to start recording, speak for 5 seconds, then listen to the AI response.
Type 'quit' to exit.
"""

import time
import torch

from src.core.config import Config
from src.core.memory import MemoryMonitor
from src.conversation.manager import ConversationManager
from src.conversation.logger import ConversationLogger
from src.audio.recorder import AudioRecorder
from src.audio.player import AudioPlayer
from src.speech.transcription import TranscriptionService
from src.speech.synthesis import SynthesisService


class ConversationPrototype:
    """Simple conversation prototype"""

    def __init__(self):
        """Initialize all components"""
        print("🚀 English Companion NX - Conversation Prototype")
        print("=" * 60)

        # Check GPU availability
        device = "cuda" if torch.cuda.is_available() and Config.USE_GPU else "cpu"
        print(f"🖥️  Device: {device.upper()}")
        if device == "cuda":
            print(f"   GPU: {torch.cuda.get_device_name(0)}")

        # Initialize audio components
        print("\n🎤 Initializing audio system...")
        self.recorder = AudioRecorder()
        self.recorder.cleanup_previous_instances()
        self.player = AudioPlayer()

        # Load models
        print("\n📦 Loading models...")
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


    def run_conversation_loop(self):
        """Run interactive conversation loop"""
        print("\n" + "=" * 60)
        print("💬 Conversation Mode")
        print("=" * 60)
        print("Instructions:")
        print("  - Press Enter to start recording")
        print("  - Speak naturally for 5 seconds")
        print("  - Listen to the AI response")
        print("  - Type 'quit' to exit")
        print("=" * 60)

        try:
            while True:
                # Wait for user to start
                user_input = input("\n▶️  Press Enter to speak (or 'quit' to exit): ").strip().lower()

                if user_input in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye!")
                    break

                try:
                    start_time = time.time()

                    # 1. Record audio
                    audio_file = self.recorder.record()

                    # 2. Transcribe
                    user_message = self.transcription.transcribe(audio_file)
                    self.recorder.cleanup_file(audio_file)

                    if not user_message:
                        print("⚠️  No speech detected. Please try again.")
                        continue

                    # 3. Generate response
                    print("💭 Thinking...")
                    llm_start = time.time()
                    response = self.conversation.generate_response(user_message)
                    llm_time = time.time() - llm_start
                    print(f"✅ Response generated ({llm_time:.2f}s)")

                    # 4. Synthesize response
                    tts_file = self.synthesis.synthesize(response)

                    # 5. Play response
                    print(f"\n🤖 Assistant: {response}\n")
                    self.player.play(tts_file)
                    self.synthesis.cleanup_file(tts_file)

                    # 6. Log conversation
                    total_time = time.time() - start_time
                    self.logger.log_exchange(
                        user_message=user_message,
                        assistant_message=response,
                        metadata={
                            "response_time_ms": int(total_time * 1000),
                            "llm_time_ms": int(llm_time * 1000)
                        }
                    )

                    # 7. Memory monitoring and cleanup
                    self.memory_monitor.on_conversation_complete()

                    # Show stats
                    print(f"\n📊 {self.conversation.get_context_summary()}")
                    print(f"💾 {self.memory_monitor.get_memory_summary()}")

                except KeyboardInterrupt:
                    print("\n\n👋 Interrupted by user. Goodbye!")
                    break
                except Exception as e:
                    print(f"\n❌ Error: {e}")
                    print("Please try again.")

        finally:
            # Show final memory statistics
            print("\n📊 Final Memory Statistics")
            self.memory_monitor.log_memory_stats()

            # Flush any remaining logs
            print("🔄 Flushing conversation logs...")
            self.logger.cleanup()

            # Final cleanup
            print("🧹 Final memory cleanup...")
            self.memory_monitor.cleanup(force=True)


def main():
    """Main entry point"""
    try:
        prototype = ConversationPrototype()
        prototype.run_conversation_loop()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
