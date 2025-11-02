#!/usr/bin/env python3
"""
Debug script for wake word detection
Shows real-time confidence scores to diagnose detection issues
"""

import struct
import time
import numpy as np
import pyaudio
from openwakeword.model import Model

# Audio configuration
# Device native rate (PowerConf S3 is 48kHz)
DEVICE_SAMPLE_RATE = 48000
# OpenWakeWord required rate
TARGET_SAMPLE_RATE = 16000
# Chunk size for 80ms at 48kHz
CHUNK_SIZE = 3840  # 80ms at 48kHz
FORMAT = pyaudio.paInt16
CHANNELS = 1

def debug_wake_word(duration=30, model_name="hey_jarvis", device_index=None):
    """
    Debug wake word detection with real-time confidence scores

    Args:
        duration: How long to listen (seconds)
        model_name: Wake word model to test
        device_index: Specific audio input device index (None = default)
    """
    print("=" * 60)
    print("WAKE WORD DEBUG MODE")
    print("=" * 60)
    print(f"Model: {model_name}")
    print(f"Duration: {duration} seconds")
    print(f"Device sample rate: {DEVICE_SAMPLE_RATE} Hz")
    print(f"Target sample rate: {TARGET_SAMPLE_RATE} Hz (OpenWakeWord)")
    print(f"Chunk size: {CHUNK_SIZE} samples ({CHUNK_SIZE/DEVICE_SAMPLE_RATE*1000:.1f}ms)")
    print("=" * 60)
    print()

    # Initialize OpenWakeWord
    print("Loading model...")
    oww_model = Model(wakeword_models=[model_name])
    print(f"✅ Model loaded: {list(oww_model.models.keys())}")
    print()

    # Initialize PyAudio
    print("Initializing audio...")
    audio = pyaudio.PyAudio()

    # List available input devices
    print("\n📱 Available audio input devices:")
    for i in range(audio.get_device_count()):
        info = audio.get_device_info_by_index(i)
        if info['maxInputChannels'] > 0:
            print(f"  [{i}] {info['name']} (channels: {info['maxInputChannels']}, rate: {info['defaultSampleRate']})")
    print()

    # Open audio stream
    try:
        if device_index is not None:
            stream = audio.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=DEVICE_SAMPLE_RATE,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=CHUNK_SIZE
            )
            device_info = audio.get_device_info_by_index(device_index)
            print(f"✅ Audio stream opened successfully")
            print(f"   Device [{device_index}]: {device_info['name']}")
        else:
            stream = audio.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=DEVICE_SAMPLE_RATE,
                input=True,
                frames_per_buffer=CHUNK_SIZE
            )
            print(f"✅ Audio stream opened successfully")
            print(f"   Device: {audio.get_default_input_device_info()['name']}")
    except Exception as e:
        print(f"❌ Failed to open audio stream: {e}")
        audio.terminate()
        return

    print()
    print("=" * 60)
    print("🎤 LISTENING... (speak 'hey jarvis' into microphone)")
    print("=" * 60)
    print()
    print("Time (s) | Audio Level | Confidence | Status")
    print("-" * 60)

    start_time = time.time()
    max_confidence = 0.0
    detection_count = 0

    try:
        while time.time() - start_time < duration:
            # Read audio chunk (at 48kHz)
            audio_data = stream.read(CHUNK_SIZE, exception_on_overflow=False)

            # Convert to numpy array
            audio_array_48k = np.frombuffer(audio_data, dtype=np.int16)
            audio_level = np.abs(audio_array_48k).mean() / 32768.0  # Normalize to 0-1

            # Downsample from 48kHz to 16kHz (3:1 ratio using decimation)
            audio_array_16k = audio_array_48k[::3]  # Take every 3rd sample

            # Get predictions from OpenWakeWord (requires 16kHz int16 numpy array)
            prediction = oww_model.predict(audio_array_16k)

            # Get confidence score for the target model
            confidence = prediction.get(model_name, 0.0)
            max_confidence = max(max_confidence, confidence)

            elapsed = time.time() - start_time

            # Print status every chunk
            status = ""
            if confidence > 0.5:
                status = "🔔 DETECTED!"
                detection_count += 1
            elif confidence > 0.3:
                status = "⚡ High confidence"
            elif audio_level > 0.01:
                status = "🎤 Audio detected"
            else:
                status = "🔇 Silent"

            print(f"{elapsed:7.2f}  | {audio_level:11.4f} | {confidence:10.4f} | {status}")

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error during detection: {e}")
        import traceback
        traceback.print_exc()
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Duration: {time.time() - start_time:.2f} seconds")
    print(f"Detections (>0.5): {detection_count}")
    print(f"Max confidence: {max_confidence:.4f}")
    print()

    if max_confidence < 0.1:
        print("⚠️  DIAGNOSIS: Very low confidence scores")
        print("   Possible issues:")
        print("   - Microphone not picking up audio")
        print("   - Audio level too low (check microphone gain)")
        print("   - Wrong audio input device selected")
        print("   - Background noise too high")
        print()
        print("   Try:")
        print("   1. Test microphone: arecord -d 5 test.wav && aplay test.wav")
        print("   2. Check audio levels: alsamixer")
        print("   3. Speak louder and closer to microphone")
    elif max_confidence < 0.3:
        print("⚠️  DIAGNOSIS: Low confidence scores")
        print("   The model is detecting some patterns but not confident enough")
        print("   Try:")
        print("   1. Speak more clearly and naturally")
        print("   2. Reduce background noise")
        print("   3. Lower threshold to 0.3 for testing")
    elif detection_count == 0:
        print("⚠️  DIAGNOSIS: High confidence but no detections")
        print(f"   Max confidence: {max_confidence:.4f} (below 0.5 threshold)")
        print("   Try:")
        print("   1. Lower threshold to 0.3")
        print("   2. Speak the wake word more clearly")
    else:
        print(f"✅ SUCCESS: Detected {detection_count} times!")


if __name__ == "__main__":
    import sys

    duration = 30
    model = "hey_jarvis"
    device = None

    if len(sys.argv) > 1:
        try:
            duration = int(sys.argv[1])
        except ValueError:
            print(f"Invalid duration: {sys.argv[1]}")
            sys.exit(1)

    if len(sys.argv) > 2:
        model = sys.argv[2]

    if len(sys.argv) > 3:
        try:
            device = int(sys.argv[3])
        except ValueError:
            print(f"Invalid device index: {sys.argv[3]}")
            sys.exit(1)

    print("Usage: python debug_wake_word.py [duration] [model] [device_index]")
    print(f"  duration: {duration} seconds")
    print(f"  model: {model}")
    print(f"  device_index: {device if device is not None else 'default'}")
    print()

    debug_wake_word(duration, model, device)
