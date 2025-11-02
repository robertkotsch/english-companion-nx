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
# OpenWakeWord required rate
TARGET_SAMPLE_RATE = 16000
FORMAT = pyaudio.paInt16
CHANNELS = 1

# Common sample rates to try (in order of preference for downsampling to 16kHz)
COMMON_SAMPLE_RATES = [16000, 48000, 44100, 32000, 24000, 22050, 8000]

def find_supported_sample_rate(audio, device_index=None):
    """
    Find a supported sample rate for the device

    Returns:
        (sample_rate, chunk_size) tuple
    """
    for rate in COMMON_SAMPLE_RATES:
        try:
            # Calculate chunk size for 80ms at this rate
            chunk_size = int(rate * 0.08)

            # Try to open stream
            stream_kwargs = {
                'format': FORMAT,
                'channels': CHANNELS,
                'rate': rate,
                'input': True,
                'frames_per_buffer': chunk_size
            }
            if device_index is not None:
                stream_kwargs['input_device_index'] = device_index

            test_stream = audio.open(**stream_kwargs)
            test_stream.close()

            print(f"✅ Found supported sample rate: {rate} Hz")
            return rate, chunk_size
        except Exception as e:
            print(f"   ❌ {rate} Hz not supported")
            continue

    raise Exception("No supported sample rate found!")

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
    print(f"Target sample rate: {TARGET_SAMPLE_RATE} Hz (OpenWakeWord)")
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

    # Find supported sample rate
    print("🔍 Auto-detecting supported sample rate...")
    try:
        device_sample_rate, chunk_size = find_supported_sample_rate(audio, device_index)
        print(f"   Device sample rate: {device_sample_rate} Hz")
        print(f"   Chunk size: {chunk_size} samples ({chunk_size/device_sample_rate*1000:.1f}ms)")
    except Exception as e:
        print(f"❌ Failed to find supported sample rate: {e}")
        audio.terminate()
        return
    print()

    # Open audio stream
    try:
        stream_kwargs = {
            'format': FORMAT,
            'channels': CHANNELS,
            'rate': device_sample_rate,
            'input': True,
            'frames_per_buffer': chunk_size
        }

        if device_index is not None:
            stream_kwargs['input_device_index'] = device_index
            device_info = audio.get_device_info_by_index(device_index)
            device_name = f"[{device_index}]: {device_info['name']}"
        else:
            device_name = audio.get_default_input_device_info()['name']

        stream = audio.open(**stream_kwargs)
        print(f"✅ Audio stream opened successfully")
        print(f"   Device: {device_name}")
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

    # Calculate downsampling ratio
    downsample_ratio = device_sample_rate // TARGET_SAMPLE_RATE if device_sample_rate != TARGET_SAMPLE_RATE else 1

    try:
        while time.time() - start_time < duration:
            # Read audio chunk at device native rate
            audio_data = stream.read(chunk_size, exception_on_overflow=False)

            # Convert to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            audio_level = np.abs(audio_array).mean() / 32768.0  # Normalize to 0-1

            # Downsample to 16kHz if necessary
            if downsample_ratio > 1:
                audio_array_16k = audio_array[::downsample_ratio]  # Decimation
            else:
                audio_array_16k = audio_array

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
