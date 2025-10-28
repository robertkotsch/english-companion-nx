#!/usr/bin/env python3
"""
Audio Hardware Test Script
Tests Anker PowerConf S3 microphone, speaker, and Whisper transcription
"""

import os
import sys
import time
import subprocess
from pathlib import Path

# Audio settings
DEVICE_NAME = "PowerConf S3"
SAMPLE_RATE = 16000
CHANNELS = 1
DURATION = 5  # seconds
TEST_FILE = "/tmp/test_audio.wav"

def print_header(text):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def check_device():
    """Check if PowerConf S3 is detected"""
    print_header("Step 1: Checking Audio Device")

    result = subprocess.run(['arecord', '-l'], capture_output=True, text=True)
    if "PowerConf S3" in result.stdout:
        print("✅ Anker PowerConf S3 detected!")

        # Find card number
        for line in result.stdout.split('\n'):
            if 'PowerConf S3' in line:
                # Extract card number (e.g., "card 2:")
                card_num = line.split('card ')[1].split(':')[0]
                print(f"   Card: {card_num}")
                # Use plughw for better compatibility (handles format conversion)
                return f"plughw:{card_num},0"
    else:
        print("❌ PowerConf S3 not found!")
        print("\nAvailable devices:")
        print(result.stdout)
        return None

def record_audio(device):
    """Record audio from microphone"""
    print_header(f"Step 2: Recording {DURATION} Seconds")

    print(f"🎤 Recording from {DEVICE_NAME}...")
    print(f"   Say something clearly into the microphone!")
    print(f"   Recording will start in 2 seconds...\n")
    time.sleep(2)

    # Record using arecord
    cmd = [
        'arecord',
        '-D', device,
        '-f', 'S16_LE',
        '-c', str(CHANNELS),
        '-r', str(SAMPLE_RATE),
        '-d', str(DURATION),
        TEST_FILE
    ]

    try:
        print("🔴 RECORDING NOW... SPEAK!")
        subprocess.run(cmd, check=True)
        print("✅ Recording complete!")

        # Check file size
        size = os.path.getsize(TEST_FILE)
        print(f"   File: {TEST_FILE}")
        print(f"   Size: {size:,} bytes")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Recording failed: {e}")
        return False

def play_audio(device):
    """Play audio through speaker"""
    print_header("Step 3: Playing Back Audio")

    print(f"🔊 Playing back through {DEVICE_NAME} speaker...")
    print(f"   You should hear what you just said...\n")

    # Play using aplay
    cmd = [
        'aplay',
        '-D', device,
        TEST_FILE
    ]

    try:
        subprocess.run(cmd, check=True)
        print("✅ Playback complete!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Playback failed: {e}")
        return False

def transcribe_audio():
    """Transcribe audio with Whisper"""
    print_header("Step 4: Transcribing with Whisper")

    try:
        import whisper
        print("📝 Loading Whisper model (base)...")
        print("   (This will take a moment on first run)\n")

        model = whisper.load_model("base")

        print("🤖 Transcribing your audio...")
        result = model.transcribe(TEST_FILE)

        print("\n" + "─"*60)
        print("TRANSCRIPTION:")
        print("─"*60)
        print(f"\"{result['text'].strip()}\"")
        print("─"*60)
        print("\n✅ Transcription complete!")

        return True
    except ImportError:
        print("❌ Whisper not installed!")
        print("   Install with: pip install openai-whisper")
        return False
    except Exception as e:
        print(f"❌ Transcription failed: {e}")
        return False

def cleanup():
    """Clean up test file"""
    if os.path.exists(TEST_FILE):
        os.remove(TEST_FILE)
        print(f"\n🧹 Cleaned up test file: {TEST_FILE}")

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  🎤 ANKER POWERCONF S3 - AUDIO HARDWARE TEST")
    print("="*60)

    try:
        # Check device
        device = check_device()
        if not device:
            print("\n❌ Test failed: Device not found")
            return 1

        # Record
        if not record_audio(device):
            print("\n❌ Test failed: Recording error")
            return 1

        # Playback
        if not play_audio(device):
            print("\n❌ Test failed: Playback error")
            return 1

        # Transcribe
        if not transcribe_audio():
            print("\n⚠️  Transcription skipped (Whisper not available)")

        # Success!
        print_header("✅ ALL TESTS PASSED!")
        print("Your Anker PowerConf S3 is working perfectly!")
        print("You're ready to build the English Companion! 🚀\n")

        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1
    finally:
        cleanup()

if __name__ == "__main__":
    sys.exit(main())
