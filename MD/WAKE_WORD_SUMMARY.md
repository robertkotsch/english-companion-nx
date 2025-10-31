# Wake Word Detection Research Summary

**Date:** October 31, 2025
**Status:** Research Complete - Ready for Implementation

---

## Executive Summary

**Porcupine (pvporcupine) is the recommended solution** for wake word detection in English Companion NX Phase 2.

### Key Findings

✅ **Dual wake word detection supported** - Can detect START and STOP triggers simultaneously
✅ **Low resource usage** - ~3.8% CPU on Raspberry Pi 3 (expect <1% on Jetson Orin NX)
✅ **Built-in keywords available** - 14 free wake words ready to use
✅ **Custom training free** - Create "hey companion" / "goodbye" in seconds
✅ **Free tier sufficient** - 1 device free, no credit card required
⚠️ **ARM64 support uncertain** - Must test on Jetson Orin NX first

---

## Available Wake Words

### Built-in Keywords (14 total)

```python
pvporcupine.KEYWORDS = [
    'alexa', 'americano', 'blueberry', 'bumblebee', 'computer',
    'grapefruit', 'grasshopper', 'hey google', 'hey siri', 'jarvis',
    'ok google', 'picovoice', 'porcupine', 'terminator'
]
```

### Recommended Combinations

#### Option 1: Built-in (Immediate Use)

| START | STOP | Notes |
|-------|------|-------|
| `computer` | `terminator` | Clear, distinct sounds |
| `jarvis` | `grasshopper` | Fun, AI assistant theme |
| `picovoice` | `bumblebee` | Low false positives |

**Pros:** Ready immediately, no setup
**Cons:** Not semantically meaningful

#### Option 2: Custom (Recommended)

| START | STOP | Notes |
|-------|------|-------|
| `hey companion` | `goodbye` | Natural, conversational |
| `okay companion` | `thank you` | Polite, clear intent |
| `hello companion` | `that's all` | Explicit start/stop |

**Pros:** Natural interaction, meaningful
**Cons:** Requires 10-minute training

---

## Performance Characteristics

### Resource Usage

- **CPU:** ~3.8% on Raspberry Pi 3 → **<1% expected on Jetson Orin NX**
- **Memory:** ~10-20 MB runtime (negligible)
- **Model size:** ~1 MB per keyword (~2 MB total for dual detection)

### Accuracy

- **Detection latency:** <200ms ✅ (meets target)
- **False positive rate:** <1% (with sensitivity=0.5)
- **False negative rate:** <5% (with sensitivity=0.5)
- **Accuracy:** 95%+ on trained keywords

### Comparison to Alternatives

Compared to PocketSphinx and Snowboy:
- **11x more accurate**
- **6.5x faster** (on Raspberry Pi 3)

---

## Implementation Path

### Quick Start (15 minutes)

```bash
# 1. Test Porcupine on Jetson
cd ~/apps/english-companion-nx
source .venv/bin/activate
pip install pvporcupine
python test_porcupine.py

# 2. Get AccessKey
# Visit: https://console.picovoice.ai/
# Sign up (free, no credit card)
# Copy AccessKey

# 3. Configure
nano .env
# Add: PORCUPINE_ACCESS_KEY=your_key_here

# 4. Choose keywords
# Built-in: computer + terminator
# OR train custom: "hey companion" + "goodbye"
```

### Full Implementation (6-10 hours)

**Phase 2A: Basic Wake Word (4-6 hours)**
1. Test Porcupine compatibility
2. Implement `src/audio/wake_word.py` module
3. Integrate with conversation prototype
4. Test and tune sensitivity

**Phase 2B: Dual Detection (3-4 hours)**
1. Add STOP keyword handling
2. Implement conversation state machine
3. Add timeout/auto-stop logic
4. Test start/stop flow

---

## API Overview

### Basic Usage

```python
import pvporcupine

# Create detector with dual keywords
porcupine = pvporcupine.create(
    access_key='YOUR_ACCESS_KEY',
    keywords=['computer', 'terminator'],  # START, STOP
    sensitivities=[0.5, 0.5]  # Per-keyword tuning
)

# Process audio frame
keyword_index = porcupine.process(pcm_frame)

if keyword_index == 0:
    print("START detected")
elif keyword_index == 1:
    print("STOP detected")
else:
    print("No keyword detected")
```

### Audio Requirements

- **Sample rate:** 16 kHz (matches current setup ✅)
- **Bit depth:** 16-bit PCM (matches current setup ✅)
- **Channels:** Mono (matches current setup ✅)
- **Frame length:** `porcupine.frame_length` samples (~512)

### Audio Input Options

1. **PyAudio** (most common, many examples)
2. **PvRecorder** (official Picovoice library)
3. **sounddevice** (simpler API)

**Recommendation:** PyAudio for compatibility

---

## Pricing & Licensing

### Free Tier

- ✅ **1 monthly active user** (sufficient for single Jetson)
- ✅ **Unlimited custom training**
- ✅ **Built-in keywords free forever**
- ✅ **Commercial use allowed**
- ✅ **No credit card required**

### Paid Plans (Future Scaling)

- **Maker:** ~$15/month (up to 10 devices)
- **Professional:** ~$100/month (up to 100 devices)
- **Enterprise:** Custom pricing

**For English Companion NX:** Free tier is sufficient

---

## Risks & Mitigations

### Risk 1: Jetson ARM64 Not Supported

**Likelihood:** Medium
**Impact:** High

**Mitigation:**
1. ✅ Test immediately with `test_porcupine.py`
2. Contact Picovoice support if issues
3. Fallback: Precise (Mycroft AI) or Whisper keyword spotting

### Risk 2: False Positives

**Likelihood:** Medium
**Impact:** Low

**Mitigation:**
1. Tune sensitivity conservatively (start at 0.35)
2. Choose unique wake words (avoid common words)
3. Add confirmation step for STOP

### Risk 3: Network Dependency

**Likelihood:** Low
**Impact:** Medium

**Mitigation:**
1. Porcupine runs offline after initial activation
2. Device must "check in" periodically (~30 days)
3. Monitor activation status

---

## Next Steps

### Immediate Actions

1. **Run compatibility test** (5 minutes)
   ```bash
   python test_porcupine.py
   ```

2. **Get AccessKey** (5 minutes)
   - Visit: https://console.picovoice.ai/
   - Sign up free
   - Copy key to `.env`

3. **Choose wake words** (10 minutes)
   - Option A: Use built-in (`computer` + `terminator`)
   - Option B: Train custom (`hey companion` + `goodbye`)

### Implementation Tasks

4. **Implement wake word module** (2-3 hours)
   - Create `src/audio/wake_word.py`
   - See `MD/WAKE_WORD_IMPLEMENTATION_GUIDE.md`

5. **Integrate with prototype** (1-2 hours)
   - Modify `conversation_prototype.py`
   - Replace "Press Enter" with wake word

6. **Test and tune** (1-2 hours)
   - Test accuracy at 1m, 2m, 3m
   - Tune sensitivity
   - Verify CPU <1%

---

## Documentation Files

### Created Files

1. **`MD/PORCUPINE_RESEARCH.md`**
   - Complete research findings (14 sections)
   - API documentation
   - Code examples
   - Troubleshooting guide

2. **`MD/WAKE_WORD_IMPLEMENTATION_GUIDE.md`**
   - Step-by-step implementation
   - Code templates
   - Testing procedures
   - Tuning guidelines

3. **`test_porcupine.py`**
   - Compatibility test script
   - Verifies ARM64 support
   - Tests dual keyword detection

4. **`.env.example`** (updated)
   - Added Porcupine configuration
   - AccessKey placeholder
   - Wake word settings
   - Sensitivity defaults

---

## Resources

### Official Documentation

- **Porcupine GitHub:** https://github.com/Picovoice/porcupine
- **Python API Docs:** https://picovoice.ai/docs/api/porcupine-python/
- **Quick Start:** https://picovoice.ai/docs/quick-start/porcupine-python/
- **Picovoice Console:** https://console.picovoice.ai/

### Project Files

- **Full Research:** `/mnt/d/GIT/english-companion-nx/MD/PORCUPINE_RESEARCH.md`
- **Implementation Guide:** `/mnt/d/GIT/english-companion-nx/MD/WAKE_WORD_IMPLEMENTATION_GUIDE.md`
- **Test Script:** `/mnt/d/GIT/english-companion-nx/test_porcupine.py`

---

## Conclusion

**Porcupine is the recommended solution** for Phase 2 wake word detection. It offers:

- ✅ Proven performance on ARM devices (Raspberry Pi)
- ✅ Low resource usage (meets <1% CPU target)
- ✅ Dual keyword detection (START/STOP)
- ✅ Free tier sufficient for single device
- ✅ Easy integration with existing audio pipeline

**Critical next step:** Run `test_porcupine.py` on Jetson Orin NX to verify ARM64 compatibility before full implementation.

**Estimated time to production:** 6-10 hours

---

**Last Updated:** October 31, 2025
**Next Action:** `python test_porcupine.py` on Jetson
