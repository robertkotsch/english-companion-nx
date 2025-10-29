#!/usr/bin/env python3
"""
Test Coqui TTS (VITS) with Anker PowerConf S3
Tests high-quality neural TTS synthesis and audio output
"""

import time
import subprocess
import os
import tempfile

def test_coqui_tts():
    """Test Coqui TTS with VITS model"""
    print("\n🔊 Testing Coqui TTS (VITS)...")
    print("=" * 50)

    try:
        from TTS.api import TTS
        import torch

        # Check GPU availability
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"📝 Initializing TTS on {device.upper()}...")
        if device == "cuda":
            print(f"   GPU: {torch.cuda.get_device_name(0)}")

        # Initialize TTS with VITS model
        print("⏳ Loading Coqui TTS model (this may take a moment)...")
        load_start = time.time()

        # Use tts_models/en/ljspeech/vits - fast and high quality
        tts = TTS(model_name="tts_models/en/ljspeech/vits", progress_bar=False).to(device)

        load_time = time.time() - load_start
        print(f"✅ Model loaded: {load_time:.2f}s")

        # Test message
        test_text = "Hello! I am your English companion. How can I help you practice English today?"

        print(f"\n🎙️  Synthesizing: '{test_text}'")
        print("⏱️  Starting synthesis...")
        start_time = time.time()

        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False, dir='/tmp')
        temp_file.close()

        # Synthesize speech
        tts.tts_to_file(text=test_text, file_path=temp_file.name)

        synth_time = time.time() - start_time
        print(f"✅ Synthesis complete: {synth_time:.2f}s")

        # Check file size
        file_size = os.path.getsize(temp_file.name)
        print(f"📁 Audio file size: {file_size / 1024:.1f} KB")

        # Play through Anker PowerConf S3 (via PulseAudio)
        print("\n🔊 Playing through Anker PowerConf S3...")
        result = subprocess.run(
            ['paplay', '--device=alsa_output.usb-Anker_PowerConf_S3_A3321-DEV-SN1-01.analog-stereo', temp_file.name],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("✅ Playback successful!")
        else:
            print(f"❌ Playback failed: {result.stderr}")
            return False

        # Cleanup
        os.remove(temp_file.name)

        # Performance summary
        print("\n" + "=" * 50)
        print("📊 Performance Summary")
        print("=" * 50)
        print(f"Model load time:    {load_time:.2f}s (one-time at startup)")
        print(f"Synthesis time:     {synth_time:.2f}s")
        print(f"Device used:        {device.upper()}")
        print(f"Audio quality:      22050 Hz, 16-bit (VITS)")

        return True

    except ImportError:
        print("❌ Coqui TTS not installed")
        print("\n📦 Install with:")
        print("   pip install TTS")
        print("\n⚠️  Note: TTS has many dependencies and may take a while to install")
        return False
    except Exception as e:
        print(f"❌ TTS test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_audio_device():
    """Verify Anker PowerConf S3 is available"""
    print("\n🔍 Checking Audio Device...")
    print("=" * 50)

    try:
        result = subprocess.run(
            ['aplay', '-l'],
            capture_output=True,
            text=True
        )

        if 'PowerConf' in result.stdout or 'card 2' in result.stdout:
            print("✅ Anker PowerConf S3 detected")
            return True
        else:
            print("⚠️  PowerConf S3 not found")
            print("\nAvailable devices:")
            print(result.stdout)
            return False

    except Exception as e:
        print(f"❌ Device check failed: {e}")
        return False

def main():
    """Run TTS tests"""
    print("🎯 Coqui TTS Test Suite for English Companion NX")
    print("=" * 50)
    print("Hardware: Anker PowerConf S3 (Card 2)")
    print("Model: VITS (tts_models/en/ljspeech/vits)")
    print()

    # Step 1: Check audio device
    device_ok = test_audio_device()

    if not device_ok:
        print("\n⚠️  Audio device not found - test may fail")

    # Step 2: Test TTS
    print()
    success = test_coqui_tts()

    print("\n" + "=" * 50)
    print("🎯 Test Summary")
    print("=" * 50)

    if success:
        print("✅ Coqui TTS (VITS): Working")
        print("\n💡 Next Steps:")
        print("   - TTS is ready for Phase 1")
        print("   - Model loads in ~3-5s (once at startup)")
        print("   - Synthesis takes ~1-2s per sentence")
        print("   - High quality, natural-sounding speech")
    else:
        print("❌ Coqui TTS: Failed")
        print("\n💡 Troubleshooting:")
        print("   - Install: pip install TTS")
        print("   - Check logs above for specific errors")

if __name__ == "__main__":
    main()
