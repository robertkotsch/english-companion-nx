#!/usr/bin/env python3
"""
Test Voice Activity Detection (VAD) recording
Tests the new silence-based recording feature

Usage:
    python test_vad_recording.py [silence_threshold] [silence_duration]

Examples:
    python test_vad_recording.py           # Default: 0.01 threshold, 1.5s silence
    python test_vad_recording.py 0.02      # Higher threshold (less sensitive)
    python test_vad_recording.py 0.01 2.0  # 2 seconds of silence before stopping
"""

import sys
from src.audio.recorder import AudioRecorder


def test_vad_recording(
    silence_threshold: float = 0.01,
    silence_duration: float = 1.5
):
    """
    Test VAD recording

    Args:
        silence_threshold: Audio level below this is considered silence
        silence_duration: Seconds of silence before stopping
    """
    print("=" * 60)
    print("VOICE ACTIVITY DETECTION (VAD) RECORDING TEST")
    print("=" * 60)
    print(f"Silence threshold: {silence_threshold:.3f}")
    print(f"Silence duration: {silence_duration}s")
    print()
    print("How it works:")
    print("  1. Say the wake word or start speaking after the beep")
    print("  2. Keep talking naturally")
    print("  3. Recording stops automatically after you stop speaking")
    print("  4. No need to time yourself!")
    print("=" * 60)
    print()

    # Initialize recorder
    print("Initializing audio recorder...")
    recorder = AudioRecorder()
    recorder.cleanup_previous_instances()
    print("✅ Ready!")
    print()

    try:
        # Test 3 recordings
        for i in range(3):
            input(f"\n▶️  Press Enter to start recording #{i+1} (or Ctrl+C to quit): ")

            try:
                # Record with VAD
                audio_file = recorder.record_with_vad(
                    silence_threshold=silence_threshold,
                    silence_duration=silence_duration,
                    min_duration=0.5,
                    max_duration=30.0
                )

                print(f"\n✅ Recording #{i+1} saved to: {audio_file}")
                print()
                print("📊 Tips:")
                print("  - If it stops too early: increase silence_duration (e.g., 2.0)")
                print("  - If it doesn't stop: lower silence_threshold (e.g., 0.005)")
                print("  - If background noise triggers: raise silence_threshold (e.g., 0.02)")

                # Cleanup
                recorder.cleanup_file(audio_file)

            except Exception as e:
                print(f"\n❌ Recording failed: {e}")

    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted. Goodbye!")

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


def main():
    """Main entry point"""
    # Parse command line arguments
    silence_threshold = 0.01
    silence_duration = 1.5

    if len(sys.argv) > 1:
        if sys.argv[1] in ["--help", "-h"]:
            print(__doc__)
            return

        try:
            silence_threshold = float(sys.argv[1])
        except ValueError:
            print(f"Invalid silence_threshold: {sys.argv[1]}")
            print("Usage: python test_vad_recording.py [silence_threshold] [silence_duration]")
            sys.exit(1)

    if len(sys.argv) > 2:
        try:
            silence_duration = float(sys.argv[2])
        except ValueError:
            print(f"Invalid silence_duration: {sys.argv[2]}")
            print("Usage: python test_vad_recording.py [silence_threshold] [silence_duration]")
            sys.exit(1)

    test_vad_recording(silence_threshold, silence_duration)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
