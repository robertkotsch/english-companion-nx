#!/usr/bin/env python3
"""
Custom Wake Word Training Helper for OpenWakeWord

This script helps you:
1. Record samples of your custom wake word
2. Generate a custom wake word model
3. Test the custom model

Requirements:
    pip install openwakeword[train]
"""

import os
import sys
import wave
import pyaudio
from pathlib import Path
from datetime import datetime

# Audio settings
SAMPLE_RATE = 16000
CHUNK_SIZE = 1280  # 80ms at 16kHz
FORMAT = pyaudio.paInt16
CHANNELS = 1


def record_sample(output_file: str, duration: float = 2.0):
    """
    Record a single wake word sample

    Args:
        output_file: Path to save WAV file
        duration: Recording duration in seconds
    """
    audio = pyaudio.PyAudio()

    # Open stream
    stream = audio.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=CHUNK_SIZE
    )

    print(f"🎤 Recording for {duration} seconds...")
    print(f"   Say your wake word clearly now!")

    frames = []
    num_chunks = int(SAMPLE_RATE / CHUNK_SIZE * duration)

    for i in range(num_chunks):
        data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
        frames.append(data)

    print("✅ Recording complete!")

    # Stop and close stream
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Save to WAV file
    with wave.open(output_file, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(b''.join(frames))

    print(f"💾 Saved to: {output_file}")


def collect_training_samples(wake_word_name: str, num_samples: int = 20):
    """
    Collect multiple samples of the wake word

    Args:
        wake_word_name: Name of your wake word (e.g., "hey_companion")
        num_samples: Number of samples to collect (recommended: 20+)
    """
    print("=" * 60)
    print(f"Custom Wake Word Training: '{wake_word_name}'")
    print("=" * 60)
    print(f"\nWe need to record {num_samples} samples of your wake word.")
    print("Tips for best results:")
    print("  - Say the wake word clearly and naturally")
    print("  - Vary your tone and speed slightly between samples")
    print("  - Record in the same environment where you'll use it")
    print("  - Minimize background noise")
    print()

    # Create output directory
    output_dir = Path("custom_wake_words") / wake_word_name
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"📁 Samples will be saved to: {output_dir}")
    print()

    input("Press ENTER to start recording...")
    print()

    for i in range(1, num_samples + 1):
        print(f"\n--- Sample {i}/{num_samples} ---")

        # Wait for user to be ready
        if i > 1:
            input("Press ENTER when ready for next recording...")

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"{wake_word_name}_{i:03d}_{timestamp}.wav"

        # Record sample
        record_sample(str(output_file), duration=2.0)

    print("\n" + "=" * 60)
    print("✅ All samples collected!")
    print("=" * 60)
    print(f"\n📁 Training data location: {output_dir}")
    print(f"   Total samples: {num_samples}")
    print(f"\nNext steps:")
    print(f"1. Review the recordings to ensure quality")
    print(f"2. Train the model using OpenWakeWord tools:")
    print(f"   (See: https://github.com/dscripka/openWakeWord)")
    print(f"\nAlternative: Use Google's Teachable Machine for quick training:")
    print(f"   https://teachablemachine.withgoogle.com/train/audio")
    print()


def quick_test_custom_model(model_path: str, duration: int = 30):
    """
    Quick test of a custom wake word model

    Args:
        model_path: Path to custom .tflite or .onnx model
        duration: Test duration in seconds
    """
    print("=" * 60)
    print(f"Testing Custom Wake Word Model")
    print("=" * 60)
    print(f"Model: {model_path}")
    print(f"Duration: {duration} seconds")
    print()

    try:
        from openwakeword.model import Model
        import numpy as np

        # Load custom model
        model = Model(custom_verifier_models=[model_path])

        # Get model name
        model_name = list(model.models.keys())[0]
        print(f"✅ Model loaded: '{model_name}'")
        print(f"   Say '{model_name}' to test detection")
        print()

        # Start audio stream
        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE
        )

        print("👂 Listening...")

        import time
        start_time = time.time()
        detections = 0

        while time.time() - start_time < duration:
            # Read audio
            audio_data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
            audio_array = np.frombuffer(audio_data, dtype=np.int16)

            # Get predictions
            predictions = model.predict(audio_array)

            # Check detection
            if model_name in predictions:
                score = predictions[model_name]
                if score > 0.5:
                    detections += 1
                    print(f"🎯 DETECTED! Score: {score:.3f}")

        # Cleanup
        stream.stop_stream()
        stream.close()
        audio.terminate()

        print("\n" + "=" * 60)
        print("Test Complete!")
        print("=" * 60)
        print(f"Detections: {detections}")
        print()

    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nMake sure you have installed openwakeword with training support:")
        print("  pip install openwakeword[train]")


def main():
    """Main menu"""
    print("\n" + "=" * 60)
    print("Custom Wake Word Training Helper")
    print("=" * 60)
    print("\nChoose an option:")
    print("1. Collect training samples for new wake word")
    print("2. Test existing custom model")
    print("3. Exit")
    print()

    choice = input("Enter choice (1-3): ").strip()

    if choice == "1":
        print("\n" + "=" * 60)
        wake_word = input("Enter your wake word phrase (e.g., 'hey companion'): ").strip().lower()
        wake_word = wake_word.replace(" ", "_")

        num_samples = input("Number of samples to collect (default: 20): ").strip()
        num_samples = int(num_samples) if num_samples else 20

        collect_training_samples(wake_word, num_samples)

    elif choice == "2":
        print("\n" + "=" * 60)
        model_path = input("Enter path to custom model (.tflite or .onnx): ").strip()

        if not os.path.exists(model_path):
            print(f"❌ Model not found: {model_path}")
            return

        duration = input("Test duration in seconds (default: 30): ").strip()
        duration = int(duration) if duration else 30

        quick_test_custom_model(model_path, duration)

    elif choice == "3":
        print("\n👋 Goodbye!")
    else:
        print("\n❌ Invalid choice")


if __name__ == "__main__":
    # Check for command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "collect":
            wake_word = sys.argv[2] if len(sys.argv) > 2 else "my_wake_word"
            num_samples = int(sys.argv[3]) if len(sys.argv) > 3 else 20
            collect_training_samples(wake_word, num_samples)

        elif command == "test":
            if len(sys.argv) < 3:
                print("Usage: python train_custom_wake_word.py test <model_path> [duration]")
                sys.exit(1)
            model_path = sys.argv[2]
            duration = int(sys.argv[3]) if len(sys.argv) > 3 else 30
            quick_test_custom_model(model_path, duration)

        else:
            print("Usage:")
            print("  python train_custom_wake_word.py collect <wake_word> [num_samples]")
            print("  python train_custom_wake_word.py test <model_path> [duration]")
            print("\nOr run without arguments for interactive menu")
    else:
        main()
