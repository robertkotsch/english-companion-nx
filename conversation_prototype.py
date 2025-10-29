#!/usr/bin/env python3
"""
English Companion NX - Conversation Prototype
Simple conversational flow: Record → Transcribe → LLM → TTS → Play

Usage:
    python conversation_prototype.py

Press Enter to start recording, speak for 5 seconds, then listen to the AI response.
Type 'quit' to exit.
"""

import os
import time
import tempfile
import subprocess
from uuid import uuid4

import whisper
import torch
import numpy as np
import soundfile as sf
from TTS.api import TTS

from src.core.config import Config
from src.conversation.manager import ConversationManager


class ConversationPrototype:
    """Simple conversation prototype"""

    def __init__(self):
        """Initialize all components"""
        print("🚀 English Companion NX - Conversation Prototype")
        print("=" * 60)

        # Check GPU availability
        self.device = "cuda" if torch.cuda.is_available() and Config.USE_GPU else "cpu"
        print(f"🖥️  Device: {self.device.upper()}")
        if self.device == "cuda":
            print(f"   GPU: {torch.cuda.get_device_name(0)}")

        # Load models
        print("\n📦 Loading models...")

        print(f"   Loading Whisper ({Config.WHISPER_MODEL})...")
        self.whisper_model = whisper.load_model(Config.WHISPER_MODEL, device=self.device)

        print(f"   Loading TTS ({Config.TTS_MODEL})...")
        self.tts = TTS(model_name=Config.TTS_MODEL, progress_bar=False).to(self.device)

        # Initialize conversation manager
        print("   Initializing conversation manager...")
        self.conversation = ConversationManager()

        print("\n✅ All systems ready!")
        print("=" * 60)

    def record_audio(self, duration: int = None) -> str:
        """
        Record audio from microphone

        Args:
            duration: Recording duration in seconds

        Returns:
            Path to recorded audio file
        """
        duration = duration or Config.AUDIO_RECORD_SECONDS

        # Generate temp file path
        temp_file = os.path.join(
            Config.AUDIO_TEMP_DIR,
            f"recording_{uuid4()}.wav"
        )

        # Countdown
        print("\n⏱️  Get ready to speak...")
        time.sleep(0.8)
        print("3...")
        time.sleep(0.6)
        print("2...")
        time.sleep(0.6)
        print("1...")
        time.sleep(0.4)

        # Start recording BEFORE the beep to avoid buffer lag
        # Record extra time to capture the beep + user speech
        buffer_time = 1.5  # Time for buffer warmup + beep + user reaction
        total_duration = duration + buffer_time

        print("🔴 RECORDING...")

        # Start recording in background
        recording_process = subprocess.Popen(
            [
                "arecord",
                "-D", Config.AUDIO_INPUT_DEVICE,
                "-f", "S16_LE",
                "-c", "1",
                "-r", str(Config.AUDIO_SAMPLE_RATE),
                "-d", str(total_duration),
                temp_file
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Wait for audio buffer to initialize properly
        time.sleep(0.5)

        # Play beep DURING recording (non-blocking)
        print("🎵 BEEP - Start speaking NOW!")
        try:
            self._play_beep()
        except Exception as e:
            print(f"⚠️  Beep failed: {e}")

        # Wait for recording to complete
        try:
            recording_process.wait(timeout=total_duration + 5)
        except subprocess.TimeoutExpired:
            recording_process.kill()
            raise Exception("Recording timeout")

        if recording_process.returncode != 0:
            # Try to get error details
            try:
                with open(temp_file, 'rb') as f:
                    if f.read(1):  # File has some content
                        print("⚠️  Recording process exited with error but file exists, continuing...")
                    else:
                        raise Exception(f"Recording failed with return code {recording_process.returncode}")
            except FileNotFoundError:
                raise Exception(f"Recording failed: no output file created (return code {recording_process.returncode})")

        # Trim the warmup period (buffer + beep, but NOT user speech)
        # Buffer warmup (0.5s) + beep (0.2s) = 0.7s trim
        trimmed_file = self._trim_audio_start(temp_file, trim_seconds=0.7)

        print("✅ Recording complete")
        return trimmed_file

    def _play_beep(self):
        """Play a short beep sound to indicate recording start"""
        try:
            # Generate a short beep tone (800Hz, 0.2 seconds)
            beep_file = os.path.join(Config.AUDIO_TEMP_DIR, "beep.wav")

            # Create beep tone using numpy
            duration = 0.2  # seconds
            frequency = 800  # Hz
            sample_rate = 22050

            t = np.linspace(0, duration, int(sample_rate * duration))
            beep = np.sin(2 * np.pi * frequency * t) * 0.3  # 30% volume

            # Save beep
            sf.write(beep_file, beep, sample_rate)

            # Play through PulseAudio (same device as TTS)
            subprocess.run(
                ["paplay", f"--device={Config.AUDIO_OUTPUT_DEVICE}", beep_file],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=1.0
            )

            # Clean up
            os.remove(beep_file)
        except Exception:
            # If beep fails, just continue (not critical)
            pass

    def _trim_audio_start(self, audio_file: str, trim_seconds: float) -> str:
        """
        Trim the beginning of an audio file

        Args:
            audio_file: Path to audio file
            trim_seconds: Seconds to trim from start

        Returns:
            Path to trimmed audio file
        """
        # Read audio
        audio_data, sample_rate = sf.read(audio_file)

        # Calculate samples to trim
        trim_samples = int(trim_seconds * sample_rate)

        # Trim the audio
        if trim_samples < len(audio_data):
            trimmed_audio = audio_data[trim_samples:]
        else:
            # If trim is longer than audio, return silence
            trimmed_audio = audio_data

        # Save trimmed audio (overwrite original)
        sf.write(audio_file, trimmed_audio, sample_rate)

        return audio_file

    def transcribe_audio(self, audio_file: str) -> str:
        """
        Transcribe audio using Whisper

        Args:
            audio_file: Path to audio file

        Returns:
            Transcribed text
        """
        print("🤖 Transcribing...")
        start_time = time.time()

        result = self.whisper_model.transcribe(
            audio_file,
            fp16=(self.device == "cuda")
        )

        transcribe_time = time.time() - start_time
        text = result["text"].strip()

        print(f"✅ Transcribed ({transcribe_time:.2f}s): \"{text}\"")
        return text

    def generate_response(self, user_message: str) -> str:
        """
        Generate AI response using LLM

        Args:
            user_message: User's message

        Returns:
            Generated response
        """
        print("💭 Thinking...")
        start_time = time.time()

        response = self.conversation.generate_response(user_message)

        generate_time = time.time() - start_time
        print(f"✅ Response generated ({generate_time:.2f}s)")

        return response

    def synthesize_speech(self, text: str) -> str:
        """
        Synthesize speech from text using TTS

        Args:
            text: Text to synthesize

        Returns:
            Path to synthesized audio file
        """
        print("🎙️  Synthesizing speech...")
        start_time = time.time()

        # Generate temp file path
        temp_file = os.path.join(
            Config.AUDIO_TEMP_DIR,
            f"tts_{uuid4()}.wav"
        )

        # Synthesize
        self.tts.tts_to_file(text=text, file_path=temp_file)

        # Add silence padding to prevent clipping
        audio_data, sample_rate = sf.read(temp_file)

        # Add 0.5 seconds of silence at the beginning
        silence_duration = 0.5
        silence_samples = int(silence_duration * sample_rate)

        # Handle mono/stereo
        if len(audio_data.shape) == 1:
            audio_data = audio_data.reshape(-1, 1)

        silence = np.zeros((silence_samples, audio_data.shape[1]))
        padded_audio = np.vstack([silence, audio_data])

        # Save padded audio
        sf.write(temp_file, padded_audio, sample_rate)

        synth_time = time.time() - start_time
        print(f"✅ Speech synthesized ({synth_time:.2f}s)")

        return temp_file

    def play_audio(self, audio_file: str):
        """
        Play audio through speaker

        Args:
            audio_file: Path to audio file
        """
        print("🔊 Playing response...")

        result = subprocess.run(
            [
                "paplay",
                f"--device={Config.AUDIO_OUTPUT_DEVICE}",
                audio_file
            ],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise Exception(f"Playback failed: {result.stderr}")

        print("✅ Playback complete")

    def cleanup_temp_file(self, file_path: str):
        """Delete temporary file"""
        try:
            os.remove(file_path)
        except Exception:
            pass

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

        while True:
            # Wait for user to start
            user_input = input("\n▶️  Press Enter to speak (or 'quit' to exit): ").strip().lower()

            if user_input in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break

            try:
                # 1. Record audio
                audio_file = self.record_audio()

                # 2. Transcribe
                user_message = self.transcribe_audio(audio_file)
                self.cleanup_temp_file(audio_file)

                if not user_message:
                    print("⚠️  No speech detected. Please try again.")
                    continue

                # 3. Generate response
                response = self.generate_response(user_message)

                # 4. Synthesize response
                tts_file = self.synthesize_speech(response)

                # 5. Play response
                print(f"\n🤖 Assistant: {response}\n")
                self.play_audio(tts_file)
                self.cleanup_temp_file(tts_file)

                # Show context info
                print(f"\n📊 {self.conversation.get_context_summary()}")

            except KeyboardInterrupt:
                print("\n\n👋 Interrupted by user. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("Please try again.")


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
