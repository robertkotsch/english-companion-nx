"""
Audio recording module for English Companion NX
Handles microphone recording with ALSA, beep generation, and cleanup
"""

import os
import time
import subprocess
import glob
from uuid import uuid4
from pathlib import Path
from typing import Optional

import numpy as np
import soundfile as sf
import pyaudio

from src.core.config import Config


class AudioRecorder:
    """Manages audio recording from microphone"""

    def __init__(self):
        """Initialize audio recorder"""
        self.active_recording = None
        self.temp_dir = Path(Config.AUDIO_TEMP_DIR)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def cleanup_previous_instances(self):
        """Kill any existing arecord processes and clean temp files"""
        try:
            # Kill any existing arecord processes
            subprocess.run(
                ["pkill", "-9", "arecord"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            # Wait for processes to die
            time.sleep(0.2)

            # Clean up temp audio files
            temp_pattern = str(self.temp_dir / "recording_*.wav")
            beep_file = self.temp_dir / "beep.wav"

            for temp_file in glob.glob(temp_pattern):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass

            try:
                beep_file.unlink(missing_ok=True)
            except Exception:
                pass

            print("🧹 Cleaned up previous instances")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")

    def record(self, duration: int = None) -> str:
        """
        Record audio from microphone

        Args:
            duration: Recording duration in seconds

        Returns:
            Path to recorded audio file
        """
        duration = duration or Config.AUDIO_RECORD_SECONDS

        # Generate temp file path
        temp_file = self.temp_dir / f"recording_{uuid4()}.wav"

        # Start recording BEFORE the beep to avoid buffer lag
        # Record extra time to capture the beep + user speech
        buffer_time = 2  # Time for buffer warmup + beep + user reaction
        total_duration = duration + buffer_time

        # Kill any existing recording processes
        if self.active_recording is not None:
            try:
                self.active_recording.kill()
            except Exception:
                pass

        # Start recording in background
        recording_process = subprocess.Popen(
            [
                "arecord",
                "-D", Config.AUDIO_INPUT_DEVICE,
                "-f", "S16_LE",
                "-c", "1",
                "-r", str(Config.AUDIO_SAMPLE_RATE),
                "-d", str(int(total_duration)),  # Must be integer for arecord
                str(temp_file)
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE
        )

        self.active_recording = recording_process

        # Wait for audio buffer to initialize
        time.sleep(0.5)

        # Play beep to signal recording start
        print("\n🔴 [BEEP] Start speaking now...")
        try:
            self.play_beep()
        except Exception as e:
            print(f"⚠️  Beep failed: {e}")

        # Ensure beep finishes
        time.sleep(0.4)

        # Wait for recording to complete
        try:
            stdout, stderr = recording_process.communicate(timeout=total_duration + 5)
        except subprocess.TimeoutExpired:
            recording_process.kill()
            self.active_recording = None
            raise Exception("Recording timeout")

        self.active_recording = None

        if recording_process.returncode != 0:
            error_msg = stderr.decode('utf-8', errors='ignore').strip() if stderr else "Unknown error"

            # Check if file exists despite error
            try:
                with open(temp_file, 'rb') as f:
                    if f.read(1):  # File has content
                        print(f"⚠️  Recording process exited with error but file exists, continuing...")
                    else:
                        raise Exception(f"Recording failed: {error_msg}")
            except FileNotFoundError:
                raise Exception(f"Recording failed: no output file - {error_msg}")

        # Trim the warmup period (buffer + beep)
        # Buffer warmup (0.5s) + beep (0.2s) + safety margin (0.3s) = 1.0s trim
        trimmed_file = self._trim_audio_start(str(temp_file), trim_seconds=1.0)

        print("✅ Recording complete")
        return trimmed_file

    def record_with_vad(
        self,
        silence_threshold: float = 0.01,
        silence_duration: float = 1.5,
        min_duration: float = 0.5,
        max_duration: float = 30.0,
        chunk_duration: float = 0.1
    ) -> str:
        """
        Record audio with Voice Activity Detection (VAD)
        Stops recording automatically when silence is detected

        Args:
            silence_threshold: Audio level below this is considered silence (0.0-1.0)
            silence_duration: Seconds of silence before stopping (e.g., 1.5s)
            min_duration: Minimum recording duration in seconds
            max_duration: Maximum recording duration in seconds (safety limit)
            chunk_duration: Duration of each audio chunk in seconds

        Returns:
            Path to recorded audio file
        """
        print("\n🎤 Recording with Voice Activity Detection...")
        print(f"   Silence threshold: {silence_threshold:.3f}")
        print(f"   Stop after {silence_duration}s of silence")
        print(f"   Max duration: {max_duration}s")

        # Initialize PyAudio
        audio = pyaudio.PyAudio()

        # Audio configuration
        device_index = 0  # PowerConf S3

        # Auto-detect supported sample rate for this device
        try:
            from src.audio.wake_word import find_supported_sample_rate
            sample_rate, _ = find_supported_sample_rate(audio, device_index)
            # Recalculate chunk_size for our desired chunk_duration (not 80ms from wake_word)
            chunk_size = int(sample_rate * chunk_duration)
            print(f"   Detected sample rate: {sample_rate} Hz")
        except ImportError:
            # Fallback: try common rates manually
            common_rates = [16000, 48000, 44100, 32000, 24000, 22050, 8000]
            sample_rate = None
            for rate in common_rates:
                try:
                    chunk_size = int(rate * chunk_duration)
                    test_stream = audio.open(
                        format=pyaudio.paInt16,
                        channels=1,
                        rate=rate,
                        input=True,
                        input_device_index=device_index,
                        frames_per_buffer=chunk_size
                    )
                    test_stream.close()
                    sample_rate = rate
                    print(f"   Detected sample rate: {sample_rate} Hz")
                    break
                except Exception:
                    continue

            if sample_rate is None:
                audio.terminate()
                raise Exception("No supported sample rate found for device")

        # Open audio stream
        try:
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=chunk_size
            )
        except Exception as e:
            audio.terminate()
            raise Exception(f"Failed to open audio stream: {e}")

        # Play beep to signal recording start
        print("🔴 [BEEP] Start speaking now...")
        try:
            self.play_beep()
        except Exception as e:
            print(f"⚠️  Beep failed: {e}")

        # Recording state
        frames = []
        start_time = time.time()
        silence_start = None
        is_speaking = False
        total_chunks = 0

        try:
            print("👂 Listening... (speak naturally, I'll stop when you're done)")

            while True:
                elapsed = time.time() - start_time

                # Safety limit - stop after max_duration
                if elapsed > max_duration:
                    print(f"\n⏱️  Maximum duration ({max_duration}s) reached")
                    break

                # Read audio chunk
                try:
                    audio_data = stream.read(chunk_size, exception_on_overflow=False)
                except Exception as e:
                    print(f"\n⚠️  Audio read error: {e}")
                    break

                # Convert to numpy array and calculate energy level
                audio_array = np.frombuffer(audio_data, dtype=np.int16)
                audio_level = np.abs(audio_array).mean() / 32768.0  # Normalize to 0-1

                # Store frame
                frames.append(audio_data)
                total_chunks += 1

                # Voice Activity Detection
                if audio_level > silence_threshold:
                    # Speech detected
                    if not is_speaking:
                        is_speaking = True
                        print("🗣️  Speech detected...")

                    silence_start = None  # Reset silence timer

                else:
                    # Silence detected
                    if is_speaking:  # Only count silence after speech started
                        if silence_start is None:
                            silence_start = time.time()
                            print("🤫 Silence detected, waiting...")

                        # Check if silence duration exceeded
                        silence_elapsed = time.time() - silence_start
                        if silence_elapsed >= silence_duration:
                            # Check minimum duration
                            if elapsed >= min_duration:
                                print(f"\n✅ Recording complete ({elapsed:.1f}s)")
                                print(f"   Detected {silence_duration}s of silence")
                                break
                            else:
                                # Too short, keep recording
                                silence_start = None

                # Progress indicator (every 1 second)
                if total_chunks % int(1.0 / chunk_duration) == 0:
                    status = "🗣️ Speaking" if audio_level > silence_threshold else "🤫 Silence"
                    print(f"   {elapsed:.1f}s | {status} | Level: {audio_level:.3f}", end='\r')

        except KeyboardInterrupt:
            print("\n\n⚠️  Recording interrupted by user")
        finally:
            # Cleanup stream
            stream.stop_stream()
            stream.close()
            audio.terminate()

        # Check if we have any audio
        if not frames:
            raise Exception("No audio recorded")

        # Convert frames to numpy array
        audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)

        # Save to temp file
        temp_file = self.temp_dir / f"recording_{uuid4()}.wav"
        sf.write(str(temp_file), audio_data, sample_rate)

        print(f"\n💾 Saved recording: {len(audio_data) / sample_rate:.1f}s")

        return str(temp_file)

    def play_beep(self):
        """Play a prominent beep sound to indicate recording start"""
        beep_file = self.temp_dir / "beep.wav"

        # Generate beep tone
        duration = 0.3  # seconds
        frequency = 700  # Hz
        sample_rate = 22050

        t = np.linspace(0, duration, int(sample_rate * duration))
        beep = np.sin(2 * np.pi * frequency * t) * 0.7  # 70% volume

        # Save beep
        sf.write(str(beep_file), beep, sample_rate)

        # Play through PulseAudio
        subprocess.run(
            ["paplay", f"--device={Config.AUDIO_OUTPUT_DEVICE}", str(beep_file)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=1.0
        )

        # Clean up
        beep_file.unlink(missing_ok=True)

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
            trimmed_audio = audio_data

        # Save trimmed audio (overwrite original)
        sf.write(audio_file, trimmed_audio, sample_rate)

        return audio_file

    def cleanup_file(self, file_path: str):
        """Delete temporary audio file"""
        try:
            os.remove(file_path)
        except Exception:
            pass
