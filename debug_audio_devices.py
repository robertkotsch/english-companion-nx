#!/usr/bin/env python3
"""
Debug script to list all available audio input devices
and test which ones work with PyAudio
"""

import pyaudio

def main():
    pa = pyaudio.PyAudio()

    print("\n" + "=" * 70)
    print("🎤 AUDIO INPUT DEVICES")
    print("=" * 70)

    default_input = None
    try:
        default_input = pa.get_default_input_device_info()
        print(f"\n✅ Default Input Device: {default_input['name']} (index: {default_input['index']})")
    except Exception as e:
        print(f"\n⚠️  No default input device found: {e}")

    print(f"\n📋 All Input Devices (Total devices: {pa.get_device_count()}):\n")

    input_devices = []
    for i in range(pa.get_device_count()):
        try:
            info = pa.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                input_devices.append((i, info))

                # Check if this is the default
                is_default = " ⭐ DEFAULT" if default_input and i == default_input['index'] else ""

                # Check if this looks like PowerConf S3
                is_powerconf = " 🎯 ANKER POWERCONF S3" if "PowerConf" in info['name'] or "Anker" in info['name'] else ""

                print(f"Device {i}: {info['name']}{is_default}{is_powerconf}")
                print(f"  Max Input Channels: {info['maxInputChannels']}")
                print(f"  Default Sample Rate: {int(info['defaultSampleRate'])} Hz")
                print()
        except Exception as e:
            print(f"Device {i}: Error reading device info - {e}")
            print()

    if not input_devices:
        print("❌ No input devices found!")
        pa.terminate()
        return

    # Test each device
    print("\n" + "=" * 70)
    print("🧪 TESTING DEVICE COMPATIBILITY")
    print("=" * 70 + "\n")

    test_rates = [16000, 48000, 44100]

    for device_idx, info in input_devices:
        device_name = info['name']
        print(f"Testing Device {device_idx}: {device_name}")

        working_rates = []
        for rate in test_rates:
            try:
                chunk_size = int(rate * 0.08)  # 80ms chunks
                stream = pa.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=rate,
                    input=True,
                    frames_per_buffer=chunk_size,
                    input_device_index=device_idx
                )
                stream.close()
                working_rates.append(rate)
                print(f"  ✅ {rate} Hz - OK")
            except Exception as e:
                print(f"  ❌ {rate} Hz - FAILED ({str(e)[:50]}...)")

        if working_rates:
            print(f"  ✅ Device {device_idx} works with sample rates: {working_rates}")
        else:
            print(f"  ❌ Device {device_idx} failed all sample rate tests")
        print()

    pa.terminate()

    # Recommendations
    print("\n" + "=" * 70)
    print("💡 RECOMMENDATIONS")
    print("=" * 70)
    print("\n1. Look for the device marked '🎯 ANKER POWERCONF S3'")
    print("2. Note its device index number")
    print("3. Update voice_assistant.py to use that index:")
    print("   assistant = VoiceAssistant(audio_device_index=X)  # Replace X with device index")
    print("\nOR run voice_assistant.py with the device index as an argument (if supported)")
    print("\n")

if __name__ == "__main__":
    main()
