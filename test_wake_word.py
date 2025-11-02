#!/usr/bin/env python3
"""
Test script for OpenWakeWord wake word detection
Tests the dual wake word system for English Companion NX
"""

import sys
import time
from src.audio.wake_word import WakeWordDetector, WakeWordType


def test_basic_detection(duration: int = 30):
    """Test basic wake word detection with 'hey_jarvis'"""
    print("=" * 60)
    print("BASIC WAKE WORD DETECTION TEST")
    print("=" * 60)
    print(f"Duration: {duration} seconds")
    print("Wake word: 'hey jarvis'")
    print("=" * 60)
    print()

    detections = []

    def on_start():
        timestamp = time.strftime("%H:%M:%S")
        detections.append(("START", timestamp))
        print(f"[{timestamp}] ✅ START callback triggered!")

    try:
        detector = WakeWordDetector(
            start_model="hey_jarvis",
            start_threshold=0.5,
            start_callback=on_start
        )

        with detector:
            print(f"👂 Listening for 'hey jarvis' for {duration} seconds...")
            print("Try saying: 'hey jarvis' to test detection")
            print()

            start_time = time.time()
            while time.time() - start_time < duration:
                result = detector.detect_once(timeout=1.0)

                if result == WakeWordType.START:
                    print("🎯 Wake word detected!")

        # Print summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        stats = detector.get_stats()
        print(f"Total detections: {stats['total_detections']}")
        print(f"Start model: {stats['start_model']}")
        print()

        if detections:
            print("Detection log:")
            for wake_type, timestamp in detections:
                print(f"  [{timestamp}] {wake_type}")
        else:
            print("No detections recorded")

        print("=" * 60)

        return stats['total_detections'] > 0

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_continuous_listening(duration: int = 60):
    """Test continuous listening mode"""
    print("\n" + "=" * 60)
    print("CONTINUOUS LISTENING TEST")
    print("=" * 60)
    print(f"Duration: {duration} seconds")
    print("Wake word: 'hey_jarvis'")
    print("Mode: Continuous (no timeout between detections)")
    print("=" * 60)
    print()

    detection_count = 0

    def on_start():
        nonlocal detection_count
        detection_count += 1
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] 🎯 Detection #{detection_count}")

    try:
        detector = WakeWordDetector(
            start_model="hey_jarvis",
            start_threshold=0.5
        )

        detector.start()
        print(f"👂 Continuous listening started...")
        print("Say 'hey jarvis' multiple times to test")
        print("Press Ctrl+C to stop early")
        print()

        # Run for specified duration
        start_time = time.time()
        try:
            while time.time() - start_time < duration:
                result = detector.detect_once(timeout=1.0)
                if result == WakeWordType.START:
                    on_start()
        except KeyboardInterrupt:
            print("\n⚠️  Interrupted by user")

        detector.stop()

        # Print summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        stats = detector.get_stats()
        print(f"Total detections: {stats['total_detections']}")
        print(f"Duration: {time.time() - start_time:.1f} seconds")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_model_availability():
    """Test which models are available"""
    print("\n" + "=" * 60)
    print("MODEL AVAILABILITY TEST")
    print("=" * 60)

    models = WakeWordDetector.list_available_models()

    if models:
        print(f"Found {len(models)} built-in models:")
        for model in models:
            print(f"  ✅ {model}")
    else:
        print("⚠️  No built-in models found")

    print("=" * 60)
    return len(models) > 0


def main():
    """Run all wake word tests"""
    print("\n" + "=" * 60)
    print("OPENWAKEWORD TEST SUITE")
    print("English Companion NX - Wake Word Detection")
    print("=" * 60)
    print()

    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help":
            print("Usage: python test_wake_word.py [TEST_TYPE] [DURATION]")
            print()
            print("TEST_TYPE:")
            print("  basic      - Basic detection test (default)")
            print("  continuous - Continuous listening test")
            print("  models     - List available models")
            print("  all        - Run all tests")
            print()
            print("DURATION: Test duration in seconds (default: 30)")
            print()
            print("Examples:")
            print("  python test_wake_word.py")
            print("  python test_wake_word.py basic 60")
            print("  python test_wake_word.py continuous")
            print("  python test_wake_word.py models")
            return

        test_type = sys.argv[1].lower()
        duration = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    else:
        test_type = "basic"
        duration = 30

    # Run tests
    results = {}

    if test_type == "models" or test_type == "all":
        results["models"] = test_model_availability()

    if test_type == "basic" or test_type == "all":
        results["basic"] = test_basic_detection(duration)

    if test_type == "continuous" or test_type == "all":
        results["continuous"] = test_continuous_listening(duration)

    # Print final summary
    if len(results) > 1:
        print("\n" + "=" * 60)
        print("FINAL SUMMARY")
        print("=" * 60)
        for test_name, passed in results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{test_name.upper()}: {status}")
        print("=" * 60)

    print("\n✅ Testing complete!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
