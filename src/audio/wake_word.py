"""
Wake word detection module for English Companion NX
Implements dual wake word detection using Porcupine (Picovoice)

START wake word: Begins conversation session
STOP wake word: Ends conversation session
"""

import struct
import time
from typing import Optional, Callable, Tuple
from enum import Enum

try:
    import pvporcupine
    PORCUPINE_AVAILABLE = True
except ImportError:
    PORCUPINE_AVAILABLE = False
    print("⚠️  pvporcupine not installed. Install with: pip install pvporcupine")

import pyaudio

from src.core.config import Config


class WakeWordType(Enum):
    """Wake word detection types"""
    START = "start"  # Trigger to begin listening
    STOP = "stop"    # Trigger to end conversation
    NONE = "none"    # No wake word detected


class WakeWordDetector:
    """
    Dual wake word detector using Porcupine

    Detects two wake words:
    - START: Triggers conversation mode (e.g., "hey companion", "computer")
    - STOP: Ends conversation mode (e.g., "goodbye", "terminator")
    """

    def __init__(
        self,
        access_key: str,
        start_keyword: str = "computer",
        stop_keyword: str = "terminator",
        start_sensitivity: float = 0.5,
        stop_sensitivity: float = 0.5,
        start_callback: Optional[Callable] = None,
        stop_callback: Optional[Callable] = None
    ):
        """
        Initialize wake word detector

        Args:
            access_key: Porcupine AccessKey from https://console.picovoice.ai/
            start_keyword: Keyword to start listening (built-in or custom)
            stop_keyword: Keyword to stop listening (built-in or custom)
            start_sensitivity: Detection sensitivity for START (0.0-1.0)
            stop_sensitivity: Detection sensitivity for STOP (0.0-1.0)
            start_callback: Optional callback when START detected
            stop_callback: Optional callback when STOP detected
        """
        if not PORCUPINE_AVAILABLE:
            raise ImportError("pvporcupine not installed. Install with: pip install pvporcupine")

        self.access_key = access_key
        self.start_keyword = start_keyword
        self.stop_keyword = stop_keyword
        self.start_sensitivity = start_sensitivity
        self.stop_sensitivity = stop_sensitivity
        self.start_callback = start_callback
        self.stop_callback = stop_callback

        # Porcupine instance
        self.porcupine: Optional[pvporcupine.Porcupine] = None

        # Audio stream
        self.audio: Optional[pyaudio.PyAudio] = None
        self.stream: Optional[pyaudio.Stream] = None

        # State
        self.running = False
        self.detection_count = {"start": 0, "stop": 0}

        print(f"🎤 Wake word detector initialized")
        print(f"   START keyword: '{start_keyword}' (sensitivity: {start_sensitivity})")
        print(f"   STOP keyword: '{stop_keyword}' (sensitivity: {stop_sensitivity})")

    def start(self):
        """Start wake word detection"""
        if self.running:
            print("⚠️  Wake word detector already running")
            return

        try:
            # Initialize Porcupine with dual keywords
            self.porcupine = pvporcupine.create(
                access_key=self.access_key,
                keywords=[self.start_keyword, self.stop_keyword],
                sensitivities=[self.start_sensitivity, self.stop_sensitivity]
            )

            # Initialize audio stream
            self.audio = pyaudio.PyAudio()

            self.stream = self.audio.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length
            )

            self.running = True
            print(f"✅ Wake word detection started")
            print(f"   Listening for '{self.start_keyword}' or '{self.stop_keyword}'...")
            print(f"   Sample rate: {self.porcupine.sample_rate} Hz")
            print(f"   Frame length: {self.porcupine.frame_length} samples")

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

        if self.porcupine:
            try:
                self.porcupine.delete()
            except Exception:
                pass
            self.porcupine = None

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
                pcm = self.stream.read(
                    self.porcupine.frame_length,
                    exception_on_overflow=False
                )
                pcm = struct.unpack_from(
                    "h" * self.porcupine.frame_length,
                    pcm
                )

                # Process with Porcupine
                keyword_index = self.porcupine.process(pcm)

                if keyword_index == 0:
                    # START keyword detected
                    self.detection_count["start"] += 1
                    print(f"🎯 START detected: '{self.start_keyword}'")

                    if self.start_callback:
                        self.start_callback()

                    return WakeWordType.START

                elif keyword_index == 1:
                    # STOP keyword detected
                    self.detection_count["stop"] += 1
                    print(f"🛑 STOP detected: '{self.stop_keyword}'")

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
                pcm = self.stream.read(
                    self.porcupine.frame_length,
                    exception_on_overflow=False
                )
                pcm = struct.unpack_from(
                    "h" * self.porcupine.frame_length,
                    pcm
                )

                keyword_index = self.porcupine.process(pcm)

                if keyword_index == 0:
                    # START keyword
                    self.detection_count["start"] += 1
                    print(f"🎯 START detected: '{self.start_keyword}'")

                    if on_start:
                        on_start()
                    elif self.start_callback:
                        self.start_callback()

                elif keyword_index == 1:
                    # STOP keyword
                    self.detection_count["stop"] += 1
                    print(f"🛑 STOP detected: '{self.stop_keyword}'")

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
            "start_keyword": self.start_keyword,
            "stop_keyword": self.stop_keyword,
            "start_detections": self.detection_count["start"],
            "stop_detections": self.detection_count["stop"],
            "total_detections": sum(self.detection_count.values()),
            "running": self.running
        }

    @staticmethod
    def list_keywords() -> list:
        """List available built-in Porcupine keywords"""
        if not PORCUPINE_AVAILABLE:
            return []

        try:
            return pvporcupine.KEYWORDS
        except Exception:
            return []

    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()


def test_wake_word_detector(access_key: str, duration: int = 30):
    """
    Test wake word detector for specified duration

    Args:
        access_key: Porcupine AccessKey
        duration: Test duration in seconds
    """
    print("=" * 60)
    print("Wake Word Detector Test")
    print("=" * 60)
    print(f"Testing for {duration} seconds...")
    print(f"Say 'computer' to test START detection")
    print(f"Say 'terminator' to test STOP detection")
    print("=" * 60)

    def on_start():
        print("✅ START callback triggered!")

    def on_stop():
        print("✅ STOP callback triggered!")

    try:
        with WakeWordDetector(
            access_key=access_key,
            start_keyword="computer",
            stop_keyword="terminator",
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

    if len(sys.argv) < 2:
        print("Usage: python -m src.audio.wake_word <ACCESS_KEY>")
        print("\nGet your AccessKey from: https://console.picovoice.ai/")
        print("\nAvailable keywords:")
        for keyword in WakeWordDetector.list_keywords():
            print(f"  - {keyword}")
        sys.exit(1)

    access_key = sys.argv[1]
    test_wake_word_detector(access_key, duration=30)
