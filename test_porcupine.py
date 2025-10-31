#!/usr/bin/env python3
"""
Quick test script for Porcupine on Jetson Orin NX
Run this to verify compatibility before implementing wake word detection

Usage:
    python test_porcupine.py
"""

import sys


def test_import():
    """Test 1: Import pvporcupine"""
    print("=" * 60)
    print("Test 1: Importing pvporcupine...")
    print("=" * 60)
    try:
        import pvporcupine
        print(f"✅ pvporcupine imported successfully")
        print(f"   Version: {pvporcupine.__version__}")
        return pvporcupine
    except ImportError as e:
        print(f"❌ Failed to import pvporcupine: {e}")
        print("\n💡 To install:")
        print("   pip install pvporcupine")
        return None


def test_keywords(pvporcupine):
    """Test 2: List built-in keywords"""
    print("\n" + "=" * 60)
    print("Test 2: Listing built-in keywords...")
    print("=" * 60)
    try:
        keywords = pvporcupine.KEYWORDS
        print(f"✅ Found {len(keywords)} built-in keywords:")
        for i, keyword in enumerate(keywords, 1):
            print(f"   {i:2d}. {keyword}")
        return keywords
    except Exception as e:
        print(f"❌ Error listing keywords: {e}")
        return None


def test_create_porcupine(pvporcupine, access_key):
    """Test 3: Initialize Porcupine with AccessKey"""
    print("\n" + "=" * 60)
    print("Test 3: Initializing Porcupine...")
    print("=" * 60)

    if access_key.lower() in ['skip', '']:
        print("⏭️  Skipped - no AccessKey provided")
        print("\n💡 To get an AccessKey:")
        print("   1. Visit: https://console.picovoice.ai/")
        print("   2. Sign up for free (no credit card required)")
        print("   3. Copy AccessKey from dashboard")
        return False

    try:
        porcupine = pvporcupine.create(
            access_key=access_key,
            keywords=['porcupine']  # Test with built-in keyword
        )

        print(f"✅ Porcupine initialized successfully!")
        print(f"   Sample rate: {porcupine.sample_rate} Hz")
        print(f"   Frame length: {porcupine.frame_length} samples")
        print(f"   Audio format: 16-bit PCM mono")

        # Cleanup
        porcupine.delete()
        return True

    except Exception as e:
        print(f"❌ Failed to initialize Porcupine: {e}")
        print("\n💡 Common issues:")
        print("   - Invalid AccessKey")
        print("   - Network connection required for first activation")
        print("   - Platform not supported (check ARM64 compatibility)")
        return False


def test_dual_keywords(pvporcupine, access_key):
    """Test 4: Test dual keyword detection"""
    print("\n" + "=" * 60)
    print("Test 4: Testing dual keyword detection...")
    print("=" * 60)

    if access_key.lower() in ['skip', '']:
        print("⏭️  Skipped - no AccessKey provided")
        return False

    try:
        porcupine = pvporcupine.create(
            access_key=access_key,
            keywords=['computer', 'terminator'],  # START and STOP
            sensitivities=[0.5, 0.5]
        )

        print(f"✅ Dual keyword detection initialized!")
        print(f"   Keyword 0 (START): 'computer' (sensitivity: 0.5)")
        print(f"   Keyword 1 (STOP): 'terminator' (sensitivity: 0.5)")
        print(f"\n💡 process() returns:")
        print(f"      -1 = no keyword detected")
        print(f"       0 = 'computer' detected")
        print(f"       1 = 'terminator' detected")

        # Cleanup
        porcupine.delete()
        return True

    except Exception as e:
        print(f"❌ Failed to initialize dual keywords: {e}")
        return False


def print_summary(tests_passed):
    """Print test summary and next steps"""
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    total = len(tests_passed)
    passed = sum(tests_passed.values())

    print(f"\nTests passed: {passed}/{total}")
    for test_name, result in tests_passed.items():
        status = "✅" if result else "❌"
        print(f"  {status} {test_name}")

    if passed == total:
        print("\n🎉 All tests passed! Porcupine is ready to use on Jetson!")
        print("\n📝 Next steps:")
        print("   1. Add AccessKey to .env:")
        print("      PORCUPINE_ACCESS_KEY=your_access_key_here")
        print("   2. Choose wake words (or train custom ones):")
        print("      PORCUPINE_START_KEYWORD=computer")
        print("      PORCUPINE_STOP_KEYWORD=terminator")
        print("   3. Implement src/audio/wake_word.py module")
        print("   4. Integrate with conversation_prototype.py")
    else:
        print("\n⚠️  Some tests failed - see errors above")
        print("\n💡 Troubleshooting:")
        print("   - Ensure pvporcupine installed: pip install pvporcupine")
        print("   - Get AccessKey: https://console.picovoice.ai/")
        print("   - Check platform support: https://picovoice.ai/docs/")

    print("=" * 60)


def main():
    """Run all tests"""
    print("\n🧪 Porcupine Wake Word Detection - Compatibility Test")
    print("   Target: Jetson Orin NX 16GB")
    print("   Project: English Companion NX - Phase 2\n")

    tests_passed = {
        "Import pvporcupine": False,
        "List built-in keywords": False,
        "Initialize Porcupine": False,
        "Dual keyword detection": False
    }

    # Test 1: Import
    pvporcupine = test_import()
    if pvporcupine:
        tests_passed["Import pvporcupine"] = True
    else:
        print_summary(tests_passed)
        return

    # Test 2: List keywords
    keywords = test_keywords(pvporcupine)
    if keywords:
        tests_passed["List built-in keywords"] = True

    # Get AccessKey
    print("\n" + "=" * 60)
    print("AccessKey Required for Tests 3-4")
    print("=" * 60)
    print("Get your free AccessKey from: https://console.picovoice.ai/")
    print("(No credit card required, 1 device free)")
    access_key = input("\nEnter AccessKey (or 'skip' to skip tests 3-4): ").strip()

    # Test 3: Initialize Porcupine
    if test_create_porcupine(pvporcupine, access_key):
        tests_passed["Initialize Porcupine"] = True

    # Test 4: Dual keywords
    if test_dual_keywords(pvporcupine, access_key):
        tests_passed["Dual keyword detection"] = True

    # Summary
    print_summary(tests_passed)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
