#!/usr/bin/env python3
"""
Test script for audio device auto-detection
Tests the find_device_by_name function from wake_word.py
"""

import pyaudio
from src.audio.wake_word import find_device_by_name

def main():
    print("🧪 Testing Audio Device Auto-Detection\n")
    print("=" * 70)

    # Initialize PyAudio
    pa = pyaudio.PyAudio()

    # Test cases
    test_patterns = [
        "PowerConf",
        "Anker",
        "USB",
        "NonExistentDevice"
    ]

    print("\n🔍 Testing device name patterns:\n")

    for pattern in test_patterns:
        print(f"Searching for: '{pattern}'")
        result = find_device_by_name(pa, pattern)

        if result is not None:
            device_info = pa.get_device_info_by_index(result)
            print(f"  ✅ FOUND at index {result}: {device_info['name']}")
            print(f"     Channels: {device_info['maxInputChannels']}, Rate: {int(device_info['defaultSampleRate'])} Hz")
        else:
            print(f"  ❌ NOT FOUND")
        print()

    pa.terminate()

    print("=" * 70)
    print("✅ Auto-detection test complete")
    print("\n💡 To use device name in voice assistant:")
    print("   python voice_assistant.py hey_jarvis alexa 0.5 0.5 PowerConf")
    print("\nOr add to .env:")
    print("   AUDIO_DEVICE_NAME=PowerConf")

if __name__ == "__main__":
    main()
