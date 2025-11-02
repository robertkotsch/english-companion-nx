"""
Wake word detection module for English Companion NX
Implements dual wake word detection using OpenWakeWord

START wake word: Begins conversation session
STOP wake word: Ends conversation session
"""

import struct
import time
import numpy as np
from typing import Optional, Callable, List
from enum import Enum
from pathlib import Path

try:
    from openwakeword.model import Model as OpenWakeWordModel
    OPENWAKEWORD_AVAILABLE = True
except ImportError:
    OPENWAKEWORD_AVAILABLE = False
    print("⚠️  openwakeword not installed. Install with: pip install openwakeword")

import pyaudio

from src.core.config import Config


class WakeWordType(Enum):
    """Wake word detection types"""
    START = "start"  # Trigger to begin listening
    STOP = "stop"    # Trigger to end conversation
    NONE = "none"    # No wake word detected


class WakeWordDetector:
    """
    Dual wake word detector using OpenWakeWord

    Detects two wake words:
    - START: Triggers conversation mode (e.g., "hey_jarvis", "alexa")
    - STOP: Ends conversation mode (can use any trained model)
    """

    def __init__(
        self,
        start_model: str = "hey_jarvis",
        stop_model: Optional[str] = None,
        start_threshold: float = 0.5,
        stop_threshold: float = 0.5,
        start_callback: Optional[Callable] = None,
        stop_callback: Optional[Callable] = None,
        custom_model_paths: Optional[List[str]] = None
    ):
        """
        Initialize wake word detector

        Args:
            start_model: Model name for START detection (built-in or custom)
            stop_model: Model name for STOP detection (optional)
            start_threshold: Detection threshold for START (0.0-1.0)
            stop_threshold: Detection threshold for STOP (0.0-1.0)
            start_callback: Optional callback when START detected
            stop_callback: Optional callback when STOP detected
            custom_model_paths: List of paths to custom .tflite or .onnx models
        """
        if not OPENWAKEWORD_AVAILABLE:
            raise ImportError("openwakeword not installed. Install with: pip install openwakeword")

        self.start_model = start_model
        self.stop_model = stop_model
        self.start_threshold = start_threshold
        self.stop_threshold = stop_threshold
        self.start_callback = start_callback
        self.stop_callback = stop_callback

        # OpenWakeWord model
        self.oww_model: Optional[OpenWakeWordModel] = None

        # Audio stream
        self.audio: Optional[pyaudio.PyAudio] = None
        self.stream: Optional[pyaudio.Stream] = None

        # State
        self.running = False
        self.detection_count = {"start": 0, "stop": 0}

        # Audio configuration (OpenWakeWord expects 16kHz, mono)
        self.sample_rate = 16000
        self.chunk_size = 1280  # 80ms chunks (recommended by OpenWakeWord)

        # Build model list
        model_list = [start_model] if start_model else []
        if stop_model:
            model_list.append(stop_model)

        # Initialize OpenWakeWord model
        try:
            if custom_model_paths:
                self.oww_model = OpenWakeWordModel(
                    wakeword_models=model_list,
                    custom_verifier_models=custom_model_paths
                )
            else:
                self.oww_model = OpenWakeWordModel(wakeword_models=model_list)

            print(f"🎤 Wake word detector initialized (OpenWakeWord)")
            print(f"   START model: '{start_model}' (threshold: {start_threshold})")
            if stop_model:
                print(f"   STOP model: '{stop_model}' (threshold: {stop_threshold})")
            print(f"   Available models: {list(self.oww_model.models.keys())}")

        except ValueError as e:
            if "Could not open" in str(e) and ".tflite" in str(e):
                raise Exception(
                    f"OpenWakeWord models not found. Please download them first:\n"
                    f"  python3 -c \"import openwakeword; openwakeword.utils.download_models()\"\n"
                    f"Original error: {e}"
                )
            raise Exception(f"Failed to initialize OpenWakeWord models: {e}")
        except Exception as e:
            raise Exception(f"Failed to initialize OpenWakeWord models: {e}")

    def start(self):
        """Start wake word detection"""
        if self.running:
            print("⚠️  Wake word detector already running")
            return

        try:
            # Initialize audio stream
            self.audio = pyaudio.PyAudio()

            self.stream = self.audio.open(
                rate=self.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.chunk_size
            )

            self.running = True
            print(f"✅ Wake word detection started")
            print(f"   Listening for '{self.start_model}'", end="")
            if self.stop_model:
                print(f" or '{self.stop_model}'...")
            else:
                print("...")
            print(f"   Sample rate: {self.sample_rate} Hz")
            print(f"   Chunk size: {self.chunk_size} samples")

        except Exception as e:
            self.cleanup()
            raise Exception(f"Failed to start wake word detector: {e}")

    def stop(self):
        """Stop wake word detection"""
        if not self.running:
            return

        self.running = False
        self.cleanup()
        print("✅ Wake word detection stopped")

    def cleanup(self):
        """Cleanup resources"""
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception:
                pass
            self.stream = None

        if self.audio:
            try:
                self.audio.terminate()
            except Exception:
                pass
            self.audio = None

    def detect_once(self, timeout: Optional[float] = None) -> WakeWordType:
        """
        Listen for wake word until one is detected or timeout

        Args:
            timeout: Maximum seconds to listen (None = infinite)

        Returns:
            WakeWordType indicating which wake word was detected
        """
        if not self.running:
            raise RuntimeError("Wake word detector not started. Call start() first.")

        start_time = time.time()

        while self.running:
            # Check timeout
            if timeout and (time.time() - start_time) > timeout:
                return WakeWordType.NONE

            try:
                # Read audio frame
                audio_data = self.stream.read(
                    self.chunk_size,
                    exception_on_overflow=False
                )

                # Convert to numpy array (int16 -> float32, normalized to [-1, 1])
                audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

                # Process with OpenWakeWord
                predictions = self.oww_model.predict(audio_array)

                # Check START model
                if self.start_model in predictions:
                    score = predictions[self.start_model]
                    if score >= self.start_threshold:
                        self.detection_count["start"] += 1
                        print(f"🎯 START detected: '{self.start_model}' (score: {score:.3f})")

                        if self.start_callback:
                            self.start_callback()

                        return WakeWordType.START

                # Check STOP model
                if self.stop_model and self.stop_model in predictions:
                    score = predictions[self.stop_model]
                    if score >= self.stop_threshold:
                        self.detection_count["stop"] += 1
                        print(f"🛑 STOP detected: '{self.stop_model}' (score: {score:.3f})")

                        if self.stop_callback:
                            self.stop_callback()

                        return WakeWordType.STOP

            except Exception as e:
                print(f"⚠️  Error during wake word detection: {e}")
                time.sleep(0.1)  # Brief pause before retry

        return WakeWordType.NONE

    def listen_continuous(
        self,
        on_start: Optional[Callable] = None,
        on_stop: Optional[Callable] = None
    ):
        """
        Continuously listen for wake words in a loop

        Args:
            on_start: Callback when START wake word detected
            on_stop: Callback when STOP wake word detected
        """
        if not self.running:
            raise RuntimeError("Wake word detector not started. Call start() first.")

        print("👂 Continuous listening mode...")

        try:
            while self.running:
                audio_data = self.stream.read(
                    self.chunk_size,
                    exception_on_overflow=False
                )

                # Convert to numpy array
                audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

                # Process with OpenWakeWord
                predictions = self.oww_model.predict(audio_array)

                # Check START model
                if self.start_model in predictions:
                    score = predictions[self.start_model]
                    if score >= self.start_threshold:
                        self.detection_count["start"] += 1
                        print(f"🎯 START detected: '{self.start_model}' (score: {score:.3f})")

                        if on_start:
                            on_start()
                        elif self.start_callback:
                            self.start_callback()

                # Check STOP model
                if self.stop_model and self.stop_model in predictions:
                    score = predictions[self.stop_model]
                    if score >= self.stop_threshold:
                        self.detection_count["stop"] += 1
                        print(f"🛑 STOP detected: '{self.stop_model}' (score: {score:.3f})")

                        if on_stop:
                            on_stop()
                        elif self.stop_callback:
                            self.stop_callback()

        except KeyboardInterrupt:
            print("\n⚠️  Continuous listening interrupted")
        except Exception as e:
            print(f"❌ Error in continuous listening: {e}")
        finally:
            self.stop()

    def get_stats(self) -> dict:
        """Get detection statistics"""
        return {
            "start_model": self.start_model,
            "stop_model": self.stop_model,
            "start_detections": self.detection_count["start"],
            "stop_detections": self.detection_count["stop"],
            "total_detections": sum(self.detection_count.values()),
            "running": self.running
        }

    @staticmethod
    def list_available_models() -> List[str]:
        """List available built-in OpenWakeWord models"""
        if not OPENWAKEWORD_AVAILABLE:
            return []

        try:
            # OpenWakeWord built-in models
            return [
                "hey_jarvis",
                "alexa",
                "hey_mycroft",
                "timer"
            ]
        except Exception:
            return []

    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()


def test_wake_word_detector(duration: int = 30):
    """
    Test wake word detector for specified duration

    Args:
        duration: Test duration in seconds
    """
    print("=" * 60)
    print("Wake Word Detector Test (OpenWakeWord)")
    print("=" * 60)
    print(f"Testing for {duration} seconds...")
    print(f"Say 'hey jarvis' to test START detection")
    print("=" * 60)

    def on_start():
        print("✅ START callback triggered!")

    def on_stop():
        print("✅ STOP callback triggered!")

    try:
        with WakeWordDetector(
            start_model="hey_jarvis",
            stop_model=None,  # No stop model for basic test
            start_threshold=0.5,
            start_callback=on_start,
            stop_callback=on_stop
        ) as detector:

            start_time = time.time()
            while time.time() - start_time < duration:
                result = detector.detect_once(timeout=1.0)

                if result != WakeWordType.NONE:
                    print(f"Detected: {result.value}")

        print("\n" + "=" * 60)
        print("Test Complete!")
        print("=" * 60)
        stats = detector.get_stats()
        print(f"START detections: {stats['start_detections']}")
        print(f"STOP detections: {stats['stop_detections']}")
        print(f"Total: {stats['total_detections']}")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")


if __name__ == "__main__":
    import sys

    print("Available OpenWakeWord models:")
    for model in WakeWordDetector.list_available_models():
        print(f"  - {model}")
    print()

    # Get duration from command line or use default
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 30

    test_wake_word_detector(duration=duration)
