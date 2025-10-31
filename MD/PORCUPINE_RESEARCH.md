# Porcupine Wake Word Detection Research

**Date:** October 31, 2025
**Project:** English Companion NX - Phase 2 Wake Word Detection
**Target Hardware:** Jetson Orin NX 16GB + Anker PowerConf S3

---

## Executive Summary

Porcupine (pvporcupine) is a suitable wake word detection library for the English Companion NX project with **dual wake word detection** support. It offers:

- ✅ **Dual wake word detection** - Can detect multiple keywords simultaneously
- ✅ **Low resource usage** - ~3.8% CPU on Raspberry Pi 3 (ARM Cortex-A53)
- ✅ **Built-in keywords** - 14 free wake words available
- ✅ **Custom wake word training** - Free instant training via Picovoice Console
- ⚠️ **Requires API key** - Free tier allows 1 monthly active user
- ⚠️ **ARM64 support uncertain** - Historical issues with Jetson Nano, need to verify current support

---

## 1. Library Overview

### Installation

```bash
pip install pvporcupine
```

**Requirements:**
- Python >= 3.9
- Valid Picovoice AccessKey (free tier available)
- Linux x86_64, macOS, Windows, Raspberry Pi (ARM64 support TBD)

### Core Features

- **On-device processing** - No cloud dependency after model download
- **Real-time detection** - Low latency (<200ms typical)
- **Deep learning powered** - High accuracy (95%+ on wake words)
- **Multiple platform support** - Linux, macOS, Windows, Raspberry Pi
- **Transfer learning** - Train custom wake words without data collection

---

## 2. Built-in Wake Words

### Available Keywords (14 total)

Access via `pvporcupine.KEYWORDS`:

```python
import pvporcupine

# List all built-in keywords
for keyword in pvporcupine.KEYWORDS:
    print(keyword)
```

**Built-in wake words:**

1. **alexa** - "Alexa"
2. **americano** - "Americano"
3. **blueberry** - "Blueberry"
4. **bumblebee** - "Bumblebee"
5. **computer** - "Computer"
6. **grapefruit** - "Grapefruit"
7. **grasshopper** - "Grasshopper"
8. **hey google** - "Hey Google"
9. **hey siri** - "Hey Siri"
10. **jarvis** - "Jarvis"
11. **ok google** - "Okay Google"
12. **picovoice** - "Picovoice"
13. **porcupine** - "Porcupine"
14. **terminator** - "Terminator"

### Recommendations for English Companion NX

#### Option 1: Use Built-in Keywords (Immediate)

**START trigger:**
- `"computer"` - Natural, assistant-like
- `"jarvis"` - Friendly AI assistant reference
- `"picovoice"` - Unique, less likely to trigger accidentally

**STOP trigger:**
- `"terminator"` - Unique end command
- `"grasshopper"` - Unusual, low false positives

**Pros:**
- ✅ Ready to use immediately
- ✅ No training required
- ✅ Well-tested models

**Cons:**
- ❌ Not semantically meaningful for start/stop
- ❌ "Computer" may trigger accidentally
- ❌ Limited customization

#### Option 2: Train Custom Wake Words (Recommended)

Use Picovoice Console to train custom phrases:

**START trigger:**
- `"hey companion"` - Natural greeting
- `"okay companion"` - Clear, conversational
- `"hello companion"` - Friendly, explicit

**STOP trigger:**
- `"thank you"` - Natural conversation ending
- `"goodbye"` - Clear intent to end
- `"that's all"` - Explicit termination

**Pros:**
- ✅ Semantically meaningful
- ✅ Natural conversation flow
- ✅ Instant training (seconds)
- ✅ Free on Picovoice Console

**Cons:**
- ❌ Requires Picovoice account setup
- ❌ Need to download .ppn model files
- ❌ More complex initial setup

---

## 3. Dual Wake Word Detection

### API Support

Porcupine **fully supports** detecting multiple wake words simultaneously:

```python
import pvporcupine

# Create handle with multiple keywords
porcupine = pvporcupine.create(
    access_key='YOUR_ACCESS_KEY',
    keywords=['computer', 'terminator'],  # START and STOP
    sensitivities=[0.5, 0.5]  # Adjust per keyword
)

# Process audio frame
keyword_index = porcupine.process(pcm_frame)

if keyword_index == 0:
    print("START trigger detected: computer")
elif keyword_index == 1:
    print("STOP trigger detected: terminator")
```

### Key Points

- **Simultaneous detection** - All keywords monitored in parallel
- **Zero overhead** - Detecting 2 vs 10 keywords has negligible CPU difference
- **Index-based results** - `process()` returns keyword index (0-based)
- **Per-keyword sensitivity** - Tune false positive/negative tradeoffs individually

### Sensitivity Tuning

```python
sensitivities=[0.5, 0.5]  # Default (balanced)
sensitivities=[0.7, 0.3]  # START more sensitive, STOP less
```

**Sensitivity range:** 0.0 to 1.0
- **Lower (0.3):** Fewer false positives, more missed detections
- **Higher (0.7):** Fewer missed detections, more false positives
- **Default (0.5):** Balanced

---

## 4. Audio Input Requirements

### Audio Format

- **Sample rate:** 16 kHz (accessed via `porcupine.sample_rate`)
- **Bit depth:** 16-bit signed PCM
- **Channels:** Mono (single channel)
- **Frame length:** Variable (accessed via `porcupine.frame_length`)

### Integration with Existing Audio System

**Current setup (Anker PowerConf S3):**
- Input device: `plughw:0,0` (ALSA)
- Sample rate: 16 kHz (matches Porcupine)
- Format: 16-bit PCM (matches Porcupine)

**Audio library options:**

1. **PyAudio** (Common in examples)
   ```python
   import pyaudio

   pa = pyaudio.PyAudio()
   stream = pa.open(
       rate=porcupine.sample_rate,
       channels=1,
       format=pyaudio.paInt16,
       input=True,
       frames_per_buffer=porcupine.frame_length
   )

   pcm = stream.read(porcupine.frame_length)
   keyword_index = porcupine.process(pcm)
   ```

2. **PvRecorder** (Picovoice's library, used in demos)
   ```python
   from pvrecorder import PvRecorder

   recorder = PvRecorder(
       frame_length=porcupine.frame_length,
       device_index=-1  # Default device
   )
   recorder.start()

   pcm = recorder.read()
   keyword_index = porcupine.process(pcm)
   ```

3. **sounddevice** (Alternative, simpler API)
   ```python
   import sounddevice as sd

   pcm = sd.rec(
       frames=porcupine.frame_length,
       samplerate=porcupine.sample_rate,
       channels=1,
       dtype='int16',
       device=Config.AUDIO_INPUT_DEVICE
   )
   keyword_index = porcupine.process(pcm.flatten())
   ```

**Recommendation:** Use **PyAudio** for consistency with potential examples, or **PvRecorder** for official Picovoice integration.

---

## 5. Performance Characteristics

### CPU Usage

**Benchmark (Raspberry Pi 3, ARM Cortex-A53):**
- **Standard model:** ~3.8% CPU per core
- **Compressed model:** ~2.5% CPU per core
- **Tiny model:** ~1.5% CPU per core

**Jetson Orin NX (ARM Cortex-A78AE, 8 cores @ 2.0 GHz):**
- Expected: **<1% CPU** (significantly more powerful than RPi3)
- Target: <1% CPU when idle (meets project requirement)

### Memory Usage

**Model sizes:**
- **Standard model:** ~1 MB per keyword
- **Compressed model:** ~500 KB per keyword
- **Tiny model:** ~300 KB per keyword

**Total memory for dual detection:**
- Standard: ~2 MB (negligible)
- Runtime RAM: ~10-20 MB (negligible compared to 16 GB total)

### Latency

- **Detection latency:** <200ms (typical)
- **Frame processing:** <10ms per frame
- **False positive rate:** <1% (with sensitivity=0.5)
- **False negative rate:** <5% (with sensitivity=0.5)

**Conclusion:** Well within target <200ms wake word detection latency.

---

## 6. Picovoice Access Key & Pricing

### Free Tier (2024)

**Sign up:** https://console.picovoice.ai/

**Free tier includes:**
- ✅ Porcupine (Wake Word): **1 monthly active user**
- ✅ Custom wake word training: **Unlimited**
- ✅ Built-in keywords: **Free forever**
- ✅ Commercial use: **Allowed on free tier**
- ✅ No credit card required
- ✅ No data collection (on-device processing)

**Limitations:**
- **1 monthly active user** - Each Jetson device counts as 1 user
- **Periodic activation** - Device must contact Picovoice server periodically
- **AccessKey required** - Must be included in code (store in .env)

### Getting Access Key

```bash
# 1. Sign up at https://console.picovoice.ai/
# 2. Copy AccessKey from dashboard
# 3. Add to .env file
echo "PORCUPINE_ACCESS_KEY=your_access_key_here" >> .env
```

### Pricing Model

**For multiple devices (future):**
- **Free tier:** 1 device
- **Maker plan:** ~$15/month (up to 10 devices)
- **Professional:** ~$100/month (up to 100 devices)
- **Enterprise:** Custom pricing

**For single Jetson Orin NX:** Free tier is sufficient.

---

## 7. Platform Support & Compatibility

### Official Support

**Confirmed platforms:**
- Linux x86_64 ✅
- macOS (x86_64, ARM64/M1) ✅
- Windows (x86_64, ARM64) ✅
- Raspberry Pi (Zero, 3, 4, 5) ✅

**Jetson Nano/Orin (ARM64 Linux):**
- ⚠️ **Historical issue:** GitHub Issue #181 reported lack of ARM64 Linux libraries for Jetson Nano
- ⚠️ **Current status unclear:** Need to verify if recent versions support Jetson Orin NX
- ✅ **Raspberry Pi works:** Similar ARM64 architecture, suggests possible support

### Testing Required

**Before full implementation:**

1. **Install pvporcupine on Jetson:**
   ```bash
   pip install pvporcupine
   ```

2. **Test basic functionality:**
   ```python
   import pvporcupine

   # Test if library loads
   print(f"Porcupine version: {pvporcupine.__version__}")
   print(f"Available keywords: {pvporcupine.KEYWORDS}")

   # Try creating handle
   try:
       porcupine = pvporcupine.create(
           access_key='YOUR_ACCESS_KEY',
           keywords=['porcupine']
       )
       print("✅ Porcupine initialized successfully")
       porcupine.delete()
   except Exception as e:
       print(f"❌ Error: {e}")
   ```

3. **Run official demo:**
   ```bash
   # Install demo dependencies
   pip install pvrecorder

   # Run microphone demo
   python -m pvporcupine_demo_mic \
       --access_key YOUR_ACCESS_KEY \
       --keywords porcupine
   ```

**If Jetson ARM64 not supported:**
- Contact Picovoice support (they're responsive)
- Consider alternative: Snowboy (older, offline), or Precise (Mycroft AI)
- Fallback: Simple energy-based voice activity detection + Whisper keyword spotting

---

## 8. Implementation Plan

### Phase 2A: Wake Word Detection (Basic)

**Goal:** Replace "Press Enter" with single wake word trigger

**Tasks:**
1. ✅ Research Porcupine (this document)
2. Test Porcupine on Jetson Orin NX
3. Get Picovoice AccessKey (free account)
4. Implement `src/audio/wake_word.py` module
5. Integrate with `conversation_prototype.py`
6. Test wake word accuracy and latency
7. Tune sensitivity for environment

**Estimated time:** 2-4 hours

### Phase 2B: Dual Wake Word Detection

**Goal:** Add STOP trigger to end conversation session

**Tasks:**
1. Train custom wake words (if needed)
2. Extend `WakeWordDetector` for dual detection
3. Add conversation state management (IDLE → LISTENING → SPEAKING)
4. Implement timeout handling (auto-stop after N minutes)
5. Test start/stop flow end-to-end

**Estimated time:** 2-3 hours

### Phase 2C: Always-On Background Service

**Goal:** Run wake word detection 24/7 as systemd service

**Tasks:**
1. Refactor to background thread/process
2. Add graceful shutdown handling
3. Implement audio device locking/sharing
4. Create systemd service file
5. Test long-term stability (24+ hours)
6. Monitor CPU/memory usage

**Estimated time:** 3-5 hours

---

## 9. Code Structure (Proposed)

### Module: `src/audio/wake_word.py`

```python
"""
Wake word detection using Porcupine
Supports dual wake word detection for START and STOP triggers
"""

import pvporcupine
from typing import Optional, Callable
from enum import Enum

from src.core.config import Config


class WakeWordType(Enum):
    """Wake word types"""
    START = "start"  # Trigger conversation start
    STOP = "stop"    # Trigger conversation end
    NONE = "none"    # No wake word detected


class WakeWordDetector:
    """
    Wake word detection with Porcupine

    Detects two wake words:
    - START: Begins listening for user speech
    - STOP: Ends conversation session
    """

    def __init__(
        self,
        start_keyword: str = 'computer',
        stop_keyword: str = 'terminator',
        start_sensitivity: float = 0.5,
        stop_sensitivity: float = 0.5
    ):
        """
        Initialize wake word detector

        Args:
            start_keyword: Built-in keyword or path to .ppn file for START
            stop_keyword: Built-in keyword or path to .ppn file for STOP
            start_sensitivity: Sensitivity for START (0.0-1.0)
            stop_sensitivity: Sensitivity for STOP (0.0-1.0)
        """
        self.start_keyword = start_keyword
        self.stop_keyword = stop_keyword

        # Initialize Porcupine with dual keywords
        self.porcupine = pvporcupine.create(
            access_key=Config.PORCUPINE_ACCESS_KEY,
            keywords=[start_keyword, stop_keyword],
            sensitivities=[start_sensitivity, stop_sensitivity]
        )

        print(f"🎤 Wake word detector initialized:")
        print(f"   START: '{start_keyword}' (sensitivity: {start_sensitivity})")
        print(f"   STOP: '{stop_keyword}' (sensitivity: {stop_sensitivity})")
        print(f"   Sample rate: {self.porcupine.sample_rate} Hz")
        print(f"   Frame length: {self.porcupine.frame_length}")

    def process_frame(self, pcm_frame: bytes) -> WakeWordType:
        """
        Process audio frame for wake word detection

        Args:
            pcm_frame: 16-bit PCM audio frame (length = frame_length)

        Returns:
            WakeWordType: START, STOP, or NONE
        """
        keyword_index = self.porcupine.process(pcm_frame)

        if keyword_index == 0:
            return WakeWordType.START
        elif keyword_index == 1:
            return WakeWordType.STOP
        else:
            return WakeWordType.NONE

    def listen_for_wake_word(
        self,
        on_start: Optional[Callable] = None,
        on_stop: Optional[Callable] = None,
        timeout: Optional[float] = None
    ) -> WakeWordType:
        """
        Continuously listen for wake words

        Args:
            on_start: Callback when START detected
            on_stop: Callback when STOP detected
            timeout: Maximum time to listen (seconds), None for infinite

        Returns:
            WakeWordType: Last detected wake word before timeout/stop
        """
        # TODO: Implement continuous listening with PyAudio or PvRecorder
        pass

    def cleanup(self):
        """Clean up Porcupine resources"""
        if self.porcupine:
            self.porcupine.delete()
            self.porcupine = None

    def __del__(self):
        """Destructor - ensure cleanup"""
        self.cleanup()


# Example usage
if __name__ == "__main__":
    import pyaudio

    detector = WakeWordDetector(
        start_keyword='computer',
        stop_keyword='terminator'
    )

    # Open audio stream
    pa = pyaudio.PyAudio()
    stream = pa.open(
        rate=detector.porcupine.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=detector.porcupine.frame_length
    )

    print("\n🎤 Listening for wake words...")
    print("   Say 'computer' to START")
    print("   Say 'terminator' to STOP")
    print("   Press Ctrl+C to exit")

    try:
        while True:
            pcm = stream.read(detector.porcupine.frame_length)
            pcm_unpacked = [int.from_bytes(pcm[i:i+2], 'little', signed=True)
                           for i in range(0, len(pcm), 2)]

            wake_word = detector.process_frame(pcm_unpacked)

            if wake_word == WakeWordType.START:
                print("✅ START wake word detected!")
            elif wake_word == WakeWordType.STOP:
                print("🛑 STOP wake word detected!")
                break

    except KeyboardInterrupt:
        print("\n👋 Exiting...")

    finally:
        stream.close()
        pa.terminate()
        detector.cleanup()
```

### Configuration Update: `.env.example`

```bash
# Porcupine Wake Word Detection (Phase 2)
PORCUPINE_ACCESS_KEY=your_access_key_here
PORCUPINE_START_KEYWORD=computer      # or path to custom .ppn file
PORCUPINE_STOP_KEYWORD=terminator     # or path to custom .ppn file
PORCUPINE_START_SENSITIVITY=0.5       # 0.0-1.0 (higher = more sensitive)
PORCUPINE_STOP_SENSITIVITY=0.5        # 0.0-1.0 (higher = more sensitive)
```

### Config Update: `src/core/config.py`

```python
# Wake word detection
PORCUPINE_ACCESS_KEY = os.getenv('PORCUPINE_ACCESS_KEY', '')
PORCUPINE_START_KEYWORD = os.getenv('PORCUPINE_START_KEYWORD', 'computer')
PORCUPINE_STOP_KEYWORD = os.getenv('PORCUPINE_STOP_KEYWORD', 'terminator')
PORCUPINE_START_SENSITIVITY = float(os.getenv('PORCUPINE_START_SENSITIVITY', '0.5'))
PORCUPINE_STOP_SENSITIVITY = float(os.getenv('PORCUPINE_STOP_SENSITIVITY', '0.5'))
```

---

## 10. Alternative Solutions (If Porcupine Fails)

### Option 1: Snowboy (Archived)

**Pros:**
- ✅ Completely offline (no API key)
- ✅ Proven on Raspberry Pi
- ✅ Custom training available

**Cons:**
- ❌ Project archived (unmaintained since 2020)
- ❌ Poor documentation
- ❌ Limited Python 3.9+ support

**Recommendation:** Only if Porcupine unavailable

### Option 2: Precise (Mycroft AI)

**Pros:**
- ✅ Open source
- ✅ Active community
- ✅ ARM support

**Cons:**
- ❌ Higher resource usage
- ❌ More complex setup
- ❌ Requires training data for custom words

**Recommendation:** Backup option

### Option 3: Whisper + Keyword Spotting

**Pros:**
- ✅ Already using Whisper
- ✅ No additional libraries
- ✅ Highly accurate

**Cons:**
- ❌ High latency (~1-2s per check)
- ❌ Higher CPU usage
- ❌ Not suitable for always-on detection

**Recommendation:** Only for non-continuous detection

### Option 4: Simple Voice Activity Detection (VAD)

**Pros:**
- ✅ Extremely low CPU (<0.1%)
- ✅ Simple implementation
- ✅ No API key required

**Cons:**
- ❌ No keyword detection (triggers on any sound)
- ❌ High false positives
- ❌ Requires manual confirmation

**Recommendation:** Fallback for always-on listening

---

## 11. Testing Checklist

### Pre-Implementation Tests

- [ ] Install pvporcupine on Jetson
- [ ] Verify ARM64 compatibility
- [ ] Test with built-in keyword (e.g., 'porcupine')
- [ ] Measure CPU usage (target: <1%)
- [ ] Test with Anker PowerConf S3 microphone
- [ ] Check latency (<200ms)
- [ ] Verify dual keyword detection works

### Implementation Tests

- [ ] START keyword detection (95%+ accuracy)
- [ ] STOP keyword detection (95%+ accuracy)
- [ ] No false positives during normal speech
- [ ] Sensitivity tuning for environment
- [ ] Long-term stability (24+ hours)
- [ ] Memory leak check (no growth over time)
- [ ] Integration with conversation loop

### Production Tests

- [ ] Background noise handling (fan, keyboard)
- [ ] Distance testing (1m, 2m, 3m from mic)
- [ ] Multiple speakers (different voices)
- [ ] Edge cases (similar-sounding words)
- [ ] Graceful failure (network, API key issues)
- [ ] Service restart recovery

---

## 12. Risks & Mitigations

### Risk 1: Jetson ARM64 Not Supported

**Likelihood:** Medium
**Impact:** High
**Mitigation:**
1. Test immediately before implementation
2. Contact Picovoice support if issues
3. Fallback to Precise or Whisper keyword spotting

### Risk 2: API Key Dependency

**Likelihood:** Low
**Impact:** Medium
**Mitigation:**
1. Store AccessKey securely in .env (chmod 600)
2. Document renewal process
3. Consider paid tier if scaling beyond 1 device

### Risk 3: False Positives

**Likelihood:** Medium
**Impact:** Low
**Mitigation:**
1. Tune sensitivity (start conservative, e.g., 0.35)
2. Add confirmation step for STOP (e.g., "Are you sure?")
3. Choose unique wake words (avoid common conversation words)

### Risk 4: Network Requirement for Activation

**Likelihood:** Low
**Impact:** Medium
**Mitigation:**
1. Test offline behavior (should work for ~30 days)
2. Monitor activation status
3. Alert if activation fails

---

## 13. Recommendations

### Immediate Next Steps

1. **Test Porcupine on Jetson** (1 hour)
   - Install pvporcupine
   - Run official demo
   - Verify ARM64 compatibility

2. **Get Picovoice AccessKey** (15 minutes)
   - Sign up at console.picovoice.ai
   - Copy AccessKey
   - Add to .env

3. **Choose Wake Words** (30 minutes)
   - Option A: Use built-in (`computer` + `terminator`)
   - Option B: Train custom (`hey companion` + `goodbye`)
   - Test accuracy in actual environment

4. **Implement Wake Word Module** (2-3 hours)
   - Create `src/audio/wake_word.py`
   - Implement dual detection
   - Add tests

5. **Integrate with Prototype** (1-2 hours)
   - Replace "Press Enter" with wake word
   - Add STOP handling
   - Test end-to-end flow

### Long-Term Considerations

1. **Scaling:**
   - If deploying to multiple Jetson devices, upgrade to Maker plan ($15/month for 10 devices)

2. **Custom Wake Words:**
   - Train "Hey Companion" and "Goodbye" for natural interaction
   - Download .ppn files and store in `models/wake_words/`

3. **Performance Optimization:**
   - Use compressed/tiny models if CPU usage >1%
   - Implement VAD to reduce processing when silent

4. **Privacy:**
   - Document that wake word detection is on-device (no cloud)
   - Mention periodic activation check to Picovoice servers

---

## 14. References

### Documentation

- **Porcupine GitHub:** https://github.com/Picovoice/porcupine
- **Python API Docs:** https://picovoice.ai/docs/api/porcupine-python/
- **Quick Start Guide:** https://picovoice.ai/docs/quick-start/porcupine-python/
- **Picovoice Console:** https://console.picovoice.ai/

### Examples

- **Microphone Demo:** https://github.com/Picovoice/porcupine/blob/master/demo/python/porcupine_demo_mic.py
- **Tutorial:** https://picovoice.ai/blog/python-wake-word-detection-tutorial/

### Benchmarks

- **Wake Word Benchmark:** https://github.com/Picovoice/wake-word-benchmark
- **Performance Data:** https://picovoice.ai/docs/benchmark/wake-word/

---

## Appendix A: Code Snippet - Testing Porcupine

```python
#!/usr/bin/env python3
"""
Quick test script for Porcupine on Jetson Orin NX
Run this to verify compatibility before implementation
"""

import sys

# Test 1: Import pvporcupine
print("Test 1: Importing pvporcupine...")
try:
    import pvporcupine
    print(f"✅ pvporcupine version: {pvporcupine.__version__}")
except ImportError as e:
    print(f"❌ Failed to import: {e}")
    print("Install with: pip install pvporcupine")
    sys.exit(1)

# Test 2: List built-in keywords
print("\nTest 2: Listing built-in keywords...")
try:
    print(f"✅ Available keywords: {pvporcupine.KEYWORDS}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 3: Initialize Porcupine (requires AccessKey)
print("\nTest 3: Initializing Porcupine...")
ACCESS_KEY = input("Enter your Picovoice AccessKey (or 'skip' to skip): ").strip()

if ACCESS_KEY.lower() != 'skip':
    try:
        porcupine = pvporcupine.create(
            access_key=ACCESS_KEY,
            keywords=['porcupine']
        )
        print(f"✅ Porcupine initialized successfully")
        print(f"   Sample rate: {porcupine.sample_rate} Hz")
        print(f"   Frame length: {porcupine.frame_length} samples")
        porcupine.delete()
    except Exception as e:
        print(f"❌ Error: {e}")
else:
    print("⏭️  Skipped (get AccessKey from https://console.picovoice.ai/)")

print("\n" + "="*60)
print("Summary:")
print("  If all tests passed, Porcupine is ready to use!")
print("  Next steps:")
print("    1. Get AccessKey from https://console.picovoice.ai/")
print("    2. Add to .env: PORCUPINE_ACCESS_KEY=your_key_here")
print("    3. Implement src/audio/wake_word.py")
print("="*60)
```

**Run on Jetson:**
```bash
python test_porcupine.py
```

---

## Appendix B: Custom Wake Word Training Steps

1. **Sign up for Picovoice Console**
   - Visit: https://console.picovoice.ai/
   - Create free account (no credit card)

2. **Navigate to Porcupine**
   - Click "Porcupine" in sidebar

3. **Create Custom Wake Word**
   - Click "Train Keyword"
   - Select language: English
   - Enter phrase: `hey companion`
   - Click "Train"

4. **Download Model**
   - Wait ~10 seconds for training
   - Download `.ppn` file
   - Save to `models/wake_words/hey-companion_en_jetson_v3_0_0.ppn`

5. **Update Configuration**
   ```bash
   # .env
   PORCUPINE_START_KEYWORD=models/wake_words/hey-companion_en_jetson_v3_0_0.ppn
   ```

6. **Repeat for STOP Keyword**
   - Train: `goodbye` or `thank you`
   - Download and configure

---

**Document End**
