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


# Common sample rates to try (in order of preference)
COMMON_SAMPLE_RATES = [16000, 48000, 44100, 32000, 24000, 22050, 8000]


def find_supported_sample_rate(audio: pyaudio.PyAudio, device_index: Optional[int] = None) -> tuple:
    """
    Find a supported sample rate for the device

    Args:
        audio: PyAudio instance
        device_index: Optional device index (None = default)

    Returns:
        (sample_rate, chunk_size) tuple

    Raises:
        Exception if no supported rate found
    """
    target_rate = 16000  # OpenWakeWord required rate

    for rate in COMMON_SAMPLE_RATES:
        try:
            # Calculate chunk size for 80ms at this rate
            chunk_size = int(rate * 0.08)

            # Try to open stream
            stream_kwargs = {
                'format': pyaudio.paInt16,
                'channels': 1,
                'rate': rate,
                'input': True,
                'frames_per_buffer': chunk_size
            }
            if device_index is not None:
                stream_kwargs['input_device_index'] = device_index

            test_stream = audio.open(**stream_kwargs)
            test_stream.close()

            return rate, chunk_size
        except Exception:
            continue

    raise Exception("No supported sample rate found for device")


def find_device_by_name(audio: pyaudio.PyAudio, device_name_pattern: str) -> Optional[int]:
    """
    Find audio input device by name pattern

    Args:
        audio: PyAudio instance
        device_name_pattern: Name pattern to search for (case-insensitive)

    Returns:
        Device index if found, None otherwise
    """
    device_name_pattern = device_name_pattern.lower()

    for i in range(audio.get_device_count()):
        try:
            info = audio.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                device_name = info['name'].lower()
                if device_name_pattern in device_name:
                    return i
        except Exception:
            continue

    return None


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
        custom_model_paths: Optional[List[str]] = None,
        audio_device_index: Optional[int] = None,
        audio_device_name: Optional[str] = None
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
            audio_device_index: PyAudio device index (None = auto-detect or use default)
            audio_device_name: Device name pattern to search for (e.g., "PowerConf")
                               If provided, overrides audio_device_index
        """
        if not OPENWAKEWORD_AVAILABLE:
            raise ImportError("openwakeword not installed. Install with: pip install openwakeword")

        self.start_model = start_model
        self.stop_model = stop_model
        self.start_threshold = start_threshold
        self.stop_threshold = stop_threshold
        self.start_callback = start_callback
        self.stop_callback = stop_callback
        self.audio_device_index = audio_device_index
        self.audio_device_name = audio_device_name

        # OpenWakeWord model
        self.oww_model: Optional[OpenWakeWordModel] = None

        # Audio stream
        self.audio: Optional[pyaudio.PyAudio] = None
        self.stream: Optional[pyaudio.Stream] = None

        # State
        self.running = False
        self.detection_count = {"start": 0, "stop": 0}
        self.last_start_detection = 0.0  # Timestamp of last START detection
        self.last_stop_detection = 0.0   # Timestamp of last STOP detection
        self.cooldown_seconds = 2.0      # Ignore detections within this window

        # Audio configuration
        self.target_sample_rate = 16000  # OpenWakeWord required rate
        self.device_sample_rate = None  # Will be detected on start()
        self.chunk_size = None  # Will be calculated based on device rate
        self.downsample_ratio = 1  # Will be calculated if needed

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

            # Auto-detect device by name if provided
            if self.audio_device_name:
                detected_index = find_device_by_name(self.audio, self.audio_device_name)
                if detected_index is not None:
                    self.audio_device_index = detected_index
                    print(f"✅ Found audio device '{self.audio_device_name}' at index {detected_index}")
                else:
                    self.audio.terminate()
                    raise Exception(
                        f"Audio device matching '{self.audio_device_name}' not found. "
                        f"Run debug_audio_devices.py to see available devices."
                    )

            # Auto-detect supported sample rate
            try:
                self.device_sample_rate, self.chunk_size = find_supported_sample_rate(
                    self.audio, self.audio_device_index
                )
            except Exception as e:
                self.audio.terminate()
                raise Exception(f"Failed to find supported sample rate: {e}")

            # Calculate downsampling ratio if needed
            self.downsample_ratio = (
                self.device_sample_rate // self.target_sample_rate
                if self.device_sample_rate != self.target_sample_rate
                else 1
            )

            # Get device name for logging
            if self.audio_device_index is not None:
                device_info = self.audio.get_device_info_by_index(self.audio_device_index)
                device_name = device_info['name']
            else:
                device_name = self.audio.get_default_input_device_info()['name']

            # Open audio stream
            stream_kwargs = {
                'rate': self.device_sample_rate,
                'channels': 1,
                'format': pyaudio.paInt16,
                'input': True,
                'frames_per_buffer': self.chunk_size
            }
            if self.audio_device_index is not None:
                stream_kwargs['input_device_index'] = self.audio_device_index

            self.stream = self.audio.open(**stream_kwargs)

            self.running = True
            print(f"✅ Wake word detection started")
            print(f"   Device: {device_name}")
            print(f"   Listening for '{self.start_model}'", end="")
            if self.stop_model:
                print(f" or '{self.stop_model}'...")
            else:
                print("...")
            print(f"   Sample rate: {self.device_sample_rate} Hz", end="")
            if self.downsample_ratio > 1:
                print(f" (downsampled to {self.target_sample_rate} Hz)")
            else:
                print()
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

                # Convert to numpy array (OpenWakeWord expects int16)
                audio_array = np.frombuffer(audio_data, dtype=np.int16)

                # Downsample to 16kHz if necessary
                if self.downsample_ratio > 1:
                    audio_array_16k = audio_array[::self.downsample_ratio]
                else:
                    audio_array_16k = audio_array

                # Process with OpenWakeWord
                predictions = self.oww_model.predict(audio_array_16k)

                # Check START model
                if self.start_model in predictions:
                    score = predictions[self.start_model]
                    if score >= self.start_threshold:
                        # Check cooldown period to avoid duplicate detections
                        current_time = time.time()
                        if current_time - self.last_start_detection >= self.cooldown_seconds:
                            self.last_start_detection = current_time
                            self.detection_count["start"] += 1
                            print(f"🎯 START detected: '{self.start_model}' (score: {score:.3f})")

                            if self.start_callback:
                                self.start_callback()

                            return WakeWordType.START

                # Check STOP model
                if self.stop_model and self.stop_model in predictions:
                    score = predictions[self.stop_model]
                    if score >= self.stop_threshold:
                        # Check cooldown period to avoid duplicate detections
                        current_time = time.time()
                        if current_time - self.last_stop_detection >= self.cooldown_seconds:
                            self.last_stop_detection = current_time
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

                # Convert to numpy array (OpenWakeWord expects int16)
                audio_array = np.frombuffer(audio_data, dtype=np.int16)

                # Downsample to 16kHz if necessary
                if self.downsample_ratio > 1:
                    audio_array_16k = audio_array[::self.downsample_ratio]
                else:
                    audio_array_16k = audio_array

                # Process with OpenWakeWord
                predictions = self.oww_model.predict(audio_array_16k)

                # Check START model
                if self.start_model in predictions:
                    score = predictions[self.start_model]
                    if score >= self.start_threshold:
                        # Check cooldown period to avoid duplicate detections
                        current_time = time.time()
                        if current_time - self.last_start_detection >= self.cooldown_seconds:
                            self.last_start_detection = current_time
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
                        # Check cooldown period to avoid duplicate detections
                        current_time = time.time()
                        if current_time - self.last_stop_detection >= self.cooldown_seconds:
                            self.last_stop_detection = current_time
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
