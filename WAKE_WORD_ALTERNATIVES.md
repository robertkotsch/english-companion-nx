# Wake Word Detection Alternatives for Jetson Orin NX

**Problem:** Porcupine (Picovoice) does not support Jetson Orin NX CPU (0xd42)

```
NotImplementedError: Unsupported CPU: '0xd42'.
```

This document evaluates alternative wake word detection solutions compatible with Jetson Orin NX.

---

## ❌ Porcupine (Picovoice) - INCOMPATIBLE

**Status:** Does not support Jetson Orin NX ARM CPU

**Error:**
```python
File "pvporcupine/_util.py", line 56, in _pv_linux_machine
    raise NotImplementedError("Unsupported CPU: '%s'." % cpu_part)
NotImplementedError: Unsupported CPU: '0xd42'.
```

**Why:** Picovoice has not added support for Orin NX's ARM Cortex-A78AE CPU (ID: 0xd42)

**Next steps:**
- Could contact Picovoice support to request Orin NX support
- Not viable for immediate implementation

---

## ✅ Recommended Alternatives (Ranked)

### Option 1: OpenWakeWord ⭐ IMPLEMENTED ✅

**Why:** Modern, actively maintained, TensorFlow Lite based, designed for edge devices

**Pros:**
- ✅ Built for edge devices (Raspberry Pi, etc.)
- ✅ Open source (Apache 2.0)
- ✅ Custom wake word training
- ✅ Low resource usage (~1-2% CPU on RPi4)
- ✅ Pre-trained models available
- ✅ Active development (2023-2024)
- ✅ TensorFlow Lite (compatible with Jetson)

**Cons:**
- ⚠️ Requires TensorFlow Lite (adds dependency)
- ⚠️ Need to verify Jetson Orin NX compatibility

**Installation:**
```bash
pip install openwakeword
pip install onnxruntime  # For optimized inference
```

**Usage:**
```python
from openwakeword.model import Model

# Load pre-trained models
owwModel = Model(wakeword_models=["hey_jarvis", "alexa"])

# Process audio
prediction = owwModel.predict(audio_data)
```

**Resources:**
- GitHub: https://github.com/dscripka/openWakeWord
- Models: https://github.com/dscripka/openWakeWord/tree/main/openwakeword/resources/models
- Pre-trained: "hey_jarvis", "alexa", "hey_mycroft", "timer"

**Implementation Status:** ✅ COMPLETE
1. ✅ Dependencies added to requirements-jetson.txt
2. ✅ WakeWordDetector class implemented in src/audio/wake_word.py
3. ✅ Test suite created (test_wake_word.py)
4. ⏳ Pending: Test on Jetson hardware
5. ⏳ Pending: Train custom "hey companion" model if needed

---

### Option 2: Whisper-Based Keyword Spotting

**Why:** We already have Whisper loaded for transcription - leverage existing model

**Pros:**
- ✅ No new dependencies
- ✅ Whisper already GPU-accelerated
- ✅ Already proven working on Jetson
- ✅ Can detect any phrase
- ✅ Flexible (any custom wake word)

**Cons:**
- ⚠️ Higher latency (~1-2s vs <200ms)
- ⚠️ More CPU/GPU usage (~5-10% vs <1%)
- ⚠️ Need to implement keyword detection logic
- ⚠️ Not as power-efficient for always-on

**Implementation approach:**
```python
# Continuous short audio captures (1-2s)
while True:
    audio = record_audio(duration=1.5)
    text = whisper.transcribe(audio)

    if "hey companion" in text.lower():
        # Start conversation
        start_conversation()
    elif "goodbye" in text.lower():
        # Stop conversation
        stop_conversation()
```

**Optimization:**
- Use Whisper "tiny" or "base" model for wake word only
- Keep "small" model for actual transcription
- Run wake word detection at lower frequency (every 2s)

**Next steps:**
1. Implement prototype
2. Measure CPU/GPU usage
3. Evaluate latency
4. Test keyword detection accuracy

---

### Option 3: Precise (Mycroft AI)

**Why:** Open source, proven on edge devices, custom training

**Pros:**
- ✅ Open source
- ✅ Designed for Raspberry Pi (should work on Jetson)
- ✅ Custom wake word training
- ✅ Used in production (Mycroft smart speakers)
- ✅ Low resource usage

**Cons:**
- ⚠️ Less actively maintained (Mycroft pivot)
- ⚠️ TensorFlow dependency
- ⚠️ Training requires audio samples
- ⚠️ May need manual setup

**Installation:**
```bash
pip install precise-runner
```

**Usage:**
```python
from precise_runner import PreciseEngine, PreciseRunner

engine = PreciseEngine('precise-engine/precise-engine', 'hey-companion.pb')
runner = PreciseRunner(engine, on_activation=lambda: print('Activated!'))
runner.start()
```

**Resources:**
- GitHub: https://github.com/MycroftAI/mycroft-precise
- Models: Need to train custom models

**Next steps:**
1. Test installation on Jetson
2. Train "hey companion" model
3. Train "goodbye" model
4. Evaluate performance

---

### Option 4: Vosk Wake Word

**Why:** Lightweight, offline, supports wake word mode

**Pros:**
- ✅ Lightweight (<50 MB models)
- ✅ Fully offline
- ✅ Built-in wake word detection
- ✅ Python bindings
- ✅ Active development

**Cons:**
- ⚠️ Less flexible than dedicated wake word solutions
- ⚠️ May have higher CPU usage
- ⚠️ Custom model training not straightforward

**Installation:**
```bash
pip install vosk
```

**Usage:**
```python
from vosk import Model, KaldiRecognizer

model = Model("/path/to/model")
rec = KaldiRecognizer(model, 16000, '["hey companion", "goodbye"]')

# Process audio
if rec.AcceptWaveform(audio):
    result = json.loads(rec.Result())
    if "hey companion" in result.get("text", ""):
        # Trigger action
```

**Resources:**
- GitHub: https://github.com/alphacep/vosk-api
- Models: https://alphacephei.com/vosk/models

**Next steps:**
1. Download small English model (~40 MB)
2. Test keyword detection
3. Evaluate CPU usage

---

### Option 5: Snowboy (Deprecated)

**Status:** ⚠️ Deprecated (but still works)

**Why:** Historic option, but no longer maintained

**Pros:**
- ✅ Lightweight
- ✅ Custom wake word training (via web interface)
- ✅ Proven on edge devices

**Cons:**
- ❌ Deprecated (Kitt.ai shut down)
- ❌ No longer maintained
- ❌ Training service offline
- ⚠️ Pre-trained models still available

**Recommendation:** Avoid unless desperate

---

## 🎯 Recommended Implementation Path

### Phase 2A: Quick Implementation (1-2 hours)

**Use Whisper-based keyword spotting**

**Why:**
- No new dependencies
- Already working on Jetson
- Flexible wake words
- Immediate implementation

**Trade-offs:**
- Higher latency (~1-2s vs <200ms)
- More power usage (~5% vs <1%)

**Implementation:**
```python
# src/audio/whisper_wake_word.py

class WhisperWakeWordDetector:
    def __init__(self, keywords: list):
        self.keywords = keywords
        self.whisper = whisper.load_model("tiny")  # Fast model

    def detect(self, audio_duration=1.5):
        audio = record_audio(audio_duration)
        result = self.whisper.transcribe(audio)
        text = result["text"].lower()

        for keyword in self.keywords:
            if keyword in text:
                return keyword

        return None
```

**Next steps:**
1. Implement `src/audio/whisper_wake_word.py`
2. Test latency and accuracy
3. Optimize audio capture frequency
4. Integrate with conversation loop

---

### Phase 2B: Production Solution (3-4 hours)

**Evaluate and implement OpenWakeWord**

**Steps:**
1. Test OpenWakeWord installation on Jetson
2. Verify TensorFlow Lite compatibility
3. Test pre-trained models ("hey_jarvis")
4. Train custom "hey companion" model if needed
5. Compare performance to Whisper approach
6. Choose best solution

**If OpenWakeWord works:**
- Lower latency (<500ms)
- Lower power usage (<2% CPU)
- Better for 24/7 operation

**If OpenWakeWord fails:**
- Fall back to Whisper approach
- Optimize for production use
- Consider hybrid approach (Whisper tiny for wake word, small for transcription)

---

## 📊 Comparison Matrix

| Solution | CPU | Latency | Custom Wake Words | Jetson Compatible | Active Dev | Recommendation |
|----------|-----|---------|-------------------|-------------------|------------|----------------|
| Porcupine | <1% | <200ms | ✅ (via web) | ❌ **NO** | ✅ | ❌ Incompatible |
| OpenWakeWord | 1-2% | 300-500ms | ✅ (train locally) | ⚠️ Unknown | ✅ | ⭐ **Test first** |
| Whisper-based | 5-10% | 1-2s | ✅ (any phrase) | ✅ **YES** | ✅ | ✅ **Quick solution** |
| Precise | 2-3% | 200-300ms | ✅ (train locally) | ⚠️ Unknown | ⚠️ | ⚠️ Backup option |
| Vosk | 3-5% | 500ms-1s | ⚠️ Limited | ✅ Likely | ✅ | ⚠️ Consider |
| Snowboy | <1% | <200ms | ❌ Service offline | ✅ Likely | ❌ | ❌ Deprecated |

---

## 💡 Recommendations

### Immediate (Today):

**Implement Whisper-based wake word detection**
- Quick to implement (1-2 hours)
- Guaranteed to work on Jetson
- Good enough for testing conversation flow
- Can optimize later

### Short-term (This week):

**Test OpenWakeWord**
- Potentially better performance
- Purpose-built for edge devices
- If it works, switch from Whisper approach

### Long-term (Future):

**Monitor Porcupine updates**
- Contact Picovoice support
- Request Jetson Orin NX support
- May be added in future release

---

## 🚀 Next Steps

1. **Implement Whisper-based wake word** (recommended for immediate progress)
   - Create `src/audio/whisper_wake_word.py`
   - Use Whisper "tiny" model for speed
   - Test with "hey companion" and "goodbye"
   - Measure latency and CPU usage

2. **Test OpenWakeWord in parallel** (potential upgrade)
   ```bash
   pip install openwakeword
   python -c "from openwakeword.model import Model; print('✅ Works!')"
   ```

3. **Document findings**
   - Update this document with test results
   - Choose final solution for Phase 2B
   - Update README with wake word approach

---

## 📝 Testing Checklist

When evaluating alternatives:

- [ ] Installation successful on Jetson
- [ ] Compatible with Python 3.10
- [ ] Works with existing audio setup (Anker PowerConf S3)
- [ ] Latency acceptable (<2s)
- [ ] CPU usage acceptable (<10%)
- [ ] Memory usage acceptable (<100MB)
- [ ] Accuracy acceptable (>90% detection rate)
- [ ] False positive rate acceptable (<5%)
- [ ] Can run 24/7 without issues
- [ ] Dual keyword support (START + STOP)

---

**Status:** ✅ OpenWakeWord IMPLEMENTED
**Implementation:** Phase 2A complete with OpenWakeWord integration
**Files:**
- `src/audio/wake_word.py` - OpenWakeWord detector class
- `test_wake_word.py` - Comprehensive test suite
- `requirements-jetson.txt` - Updated with OpenWakeWord dependencies

**Next Steps:**
1. Test on Jetson Orin NX hardware
2. Verify TFLite compatibility and performance
3. Train custom "hey companion" model if needed
4. Integrate with main conversation loop

**Last Updated:** 2025-01-15 (OpenWakeWord implementation complete)
