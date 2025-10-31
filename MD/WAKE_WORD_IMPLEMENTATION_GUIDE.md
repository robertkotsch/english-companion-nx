# Wake Word Implementation Guide

**Phase 2: Dual Wake Word Detection**
**Target:** Replace "Press Enter" mode with always-on wake word listening

---

## Quick Start

### 1. Test Porcupine Compatibility (5 minutes)

```bash
# On Jetson Orin NX
cd ~/apps/english-companion-nx
source .venv/bin/activate

# Install Porcupine
pip install pvporcupine

# Run compatibility test
python test_porcupine.py
```

**Expected output:**
- ✅ Import successful
- ✅ 14 built-in keywords listed
- ✅ Porcupine initialized (requires AccessKey)
- ✅ Dual keyword detection works

### 2. Get Picovoice AccessKey (5 minutes)

1. Visit: https://console.picovoice.ai/
2. Sign up (free, no credit card)
3. Copy AccessKey from dashboard
4. Add to `.env`:

```bash
# Wake Word Detection (Phase 2)
PORCUPINE_ACCESS_KEY=your_access_key_here
PORCUPINE_START_KEYWORD=computer      # Built-in keyword
PORCUPINE_STOP_KEYWORD=terminator     # Built-in keyword
PORCUPINE_START_SENSITIVITY=0.5       # 0.0-1.0
PORCUPINE_STOP_SENSITIVITY=0.5        # 0.0-1.0
```

### 3. Choose Wake Words (10 minutes)

#### Option A: Built-in Keywords (Immediate)

**Recommended combinations:**

| START Keyword | STOP Keyword | Notes |
|--------------|--------------|-------|
| `computer` | `terminator` | Clear, distinct |
| `jarvis` | `grasshopper` | Unique, fun |
| `picovoice` | `bumblebee` | Low false positives |

**Pros:**
- ✅ Ready to use immediately
- ✅ No training required

**Cons:**
- ❌ Not semantically meaningful
- ❌ May feel artificial

#### Option B: Custom Keywords (Recommended)

**Train custom wake words** for natural interaction:

| START Keyword | STOP Keyword | Notes |
|--------------|--------------|-------|
| `hey companion` | `goodbye` | Natural, conversational |
| `okay companion` | `thank you` | Polite, clear intent |
| `hello companion` | `that's all` | Explicit start/stop |

**Training process (10 minutes):**

1. Go to: https://console.picovoice.ai/
2. Navigate to "Porcupine" → "Train Keyword"
3. Select language: English
4. Enter phrase: `hey companion`
5. Click "Train" (takes ~10 seconds)
6. Download `.ppn` file
7. Save to `models/wake_words/hey-companion_en_jetson_v3_0_0.ppn`
8. Repeat for STOP keyword

**Update `.env`:**
```bash
PORCUPINE_START_KEYWORD=models/wake_words/hey-companion_en_jetson_v3_0_0.ppn
PORCUPINE_STOP_KEYWORD=models/wake_words/goodbye_en_jetson_v3_0_0.ppn
```

---

## Implementation Steps

### Step 1: Update Configuration (5 minutes)

**Edit `src/core/config.py`:**

```python
# Wake word detection (Phase 2)
PORCUPINE_ACCESS_KEY = os.getenv('PORCUPINE_ACCESS_KEY', '')
PORCUPINE_START_KEYWORD = os.getenv('PORCUPINE_START_KEYWORD', 'computer')
PORCUPINE_STOP_KEYWORD = os.getenv('PORCUPINE_STOP_KEYWORD', 'terminator')
PORCUPINE_START_SENSITIVITY = float(os.getenv('PORCUPINE_START_SENSITIVITY', '0.5'))
PORCUPINE_STOP_SENSITIVITY = float(os.getenv('PORCUPINE_STOP_SENSITIVITY', '0.5'))
```

### Step 2: Create Wake Word Module (1 hour)

**Create `src/audio/wake_word.py`:**

See `/mnt/d/GIT/english-companion-nx/MD/PORCUPINE_RESEARCH.md` Section 9 for complete implementation.

**Key components:**

```python
class WakeWordType(Enum):
    START = "start"
    STOP = "stop"
    NONE = "none"

class WakeWordDetector:
    def __init__(self, start_keyword, stop_keyword):
        self.porcupine = pvporcupine.create(
            access_key=Config.PORCUPINE_ACCESS_KEY,
            keywords=[start_keyword, stop_keyword],
            sensitivities=[start_sensitivity, stop_sensitivity]
        )

    def process_frame(self, pcm_frame) -> WakeWordType:
        keyword_index = self.porcupine.process(pcm_frame)
        if keyword_index == 0:
            return WakeWordType.START
        elif keyword_index == 1:
            return WakeWordType.STOP
        else:
            return WakeWordType.NONE
```

### Step 3: Add Audio Streaming (1 hour)

**Option A: Using PyAudio** (most common)

```python
import pyaudio

class WakeWordDetector:
    def listen_continuous(self, on_start, on_stop):
        """Continuously listen for wake words"""
        pa = pyaudio.PyAudio()
        stream = pa.open(
            rate=self.porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            input_device_index=self._get_device_index(),
            frames_per_buffer=self.porcupine.frame_length
        )

        try:
            while self.running:
                pcm = stream.read(self.porcupine.frame_length)
                pcm_unpacked = self._unpack_pcm(pcm)
                wake_word = self.process_frame(pcm_unpacked)

                if wake_word == WakeWordType.START:
                    on_start()
                elif wake_word == WakeWordType.STOP:
                    on_stop()

        finally:
            stream.close()
            pa.terminate()
```

**Option B: Using PvRecorder** (official Picovoice library)

```python
from pvrecorder import PvRecorder

class WakeWordDetector:
    def listen_continuous(self, on_start, on_stop):
        """Continuously listen for wake words"""
        recorder = PvRecorder(
            frame_length=self.porcupine.frame_length,
            device_index=-1  # Default device
        )
        recorder.start()

        try:
            while self.running:
                pcm = recorder.read()
                wake_word = self.process_frame(pcm)

                if wake_word == WakeWordType.START:
                    on_start()
                elif wake_word == WakeWordType.STOP:
                    on_stop()

        finally:
            recorder.delete()
```

### Step 4: Integrate with Conversation Prototype (1 hour)

**Modify `conversation_prototype.py`:**

```python
from src.audio.wake_word import WakeWordDetector, WakeWordType

class ConversationPrototype:
    def __init__(self):
        # ... existing initialization ...

        # Add wake word detector
        print("\n🎤 Initializing wake word detection...")
        self.wake_word = WakeWordDetector(
            start_keyword=Config.PORCUPINE_START_KEYWORD,
            stop_keyword=Config.PORCUPINE_STOP_KEYWORD
        )

    def run_conversation_loop(self):
        """Run always-on conversation loop with wake words"""
        print("\n💬 Always-On Mode - Listening for wake words...")
        print(f"   Say '{Config.PORCUPINE_START_KEYWORD}' to start")
        print(f"   Say '{Config.PORCUPINE_STOP_KEYWORD}' to stop")

        try:
            while True:
                # Listen for START wake word
                print("\n🎧 Listening...")
                wake_word = self.wake_word.listen_for_wake_word()

                if wake_word == WakeWordType.START:
                    print("✅ START detected!")
                    self.handle_conversation()

                elif wake_word == WakeWordType.STOP:
                    print("🛑 STOP detected - Goodbye!")
                    break

        except KeyboardInterrupt:
            print("\n👋 Exiting...")
        finally:
            self.wake_word.cleanup()

    def handle_conversation(self):
        """Handle single conversation exchange"""
        # 1. Record audio (existing code)
        audio_file = self.recorder.record()

        # 2. Transcribe (existing code)
        user_message = self.transcription.transcribe(audio_file)
        self.recorder.cleanup_file(audio_file)

        # 3. Generate response (existing code)
        response = self.conversation.generate_response(user_message)

        # 4. Synthesize speech (existing code)
        audio_file = self.synthesis.synthesize(response)

        # 5. Play response (existing code)
        self.player.play(audio_file)
        self.synthesis.cleanup_file(audio_file)
```

### Step 5: Add Conversation State Management (30 minutes)

**Track conversation state:**

```python
from enum import Enum

class ConversationState(Enum):
    IDLE = "idle"           # Waiting for START wake word
    LISTENING = "listening" # Recording user speech
    PROCESSING = "processing" # Transcribing + LLM generation
    SPEAKING = "speaking"   # Playing TTS response
    ENDED = "ended"         # STOP wake word detected

class ConversationPrototype:
    def __init__(self):
        # ... existing ...
        self.state = ConversationState.IDLE

    def run_conversation_loop(self):
        """State-based conversation loop"""
        while self.state != ConversationState.ENDED:
            if self.state == ConversationState.IDLE:
                self.wait_for_start_trigger()

            elif self.state == ConversationState.LISTENING:
                self.record_user_speech()

            elif self.state == ConversationState.PROCESSING:
                self.generate_response()

            elif self.state == ConversationState.SPEAKING:
                self.play_response()

    def wait_for_start_trigger(self):
        """Wait for START wake word"""
        wake_word = self.wake_word.listen_for_wake_word(timeout=None)

        if wake_word == WakeWordType.START:
            self.state = ConversationState.LISTENING
        elif wake_word == WakeWordType.STOP:
            self.state = ConversationState.ENDED
```

---

## Testing

### Unit Tests

**Test wake word detection:**

```python
# tests/test_wake_word.py
import pytest
from src.audio.wake_word import WakeWordDetector, WakeWordType

def test_wake_word_initialization():
    """Test detector initializes correctly"""
    detector = WakeWordDetector('computer', 'terminator')
    assert detector.porcupine is not None
    detector.cleanup()

def test_dual_keyword_detection():
    """Test dual keyword detection"""
    detector = WakeWordDetector('computer', 'terminator')

    # Mock audio frames (would need actual audio in practice)
    # ...

    detector.cleanup()

def test_sensitivity_tuning():
    """Test sensitivity adjustment"""
    detector = WakeWordDetector(
        'computer', 'terminator',
        start_sensitivity=0.7,
        stop_sensitivity=0.3
    )
    assert detector.start_sensitivity == 0.7
    assert detector.stop_sensitivity == 0.3
    detector.cleanup()
```

### Manual Testing

**Test 1: Wake word accuracy**

```bash
python test_wake_word.py
# Say START keyword 10 times → should detect 9-10 times
# Say STOP keyword 10 times → should detect 9-10 times
# Talk normally (no keywords) → should NOT detect
```

**Test 2: False positive rate**

```bash
# Have normal conversation for 5 minutes
# Should NOT trigger accidentally
# Measure: false positives per hour
```

**Test 3: Distance testing**

```bash
# Test at 1m, 2m, 3m from microphone
# Detection rate should be >90% at 2m
```

**Test 4: CPU usage**

```bash
# Monitor CPU while idle
top -p $(pgrep -f conversation_prototype)
# Should be <1% CPU when listening
```

**Test 5: Long-term stability**

```bash
# Run for 24 hours
# Check for memory leaks, crashes
```

---

## Tuning & Optimization

### Sensitivity Adjustment

**Start conservative (0.35):**
```bash
PORCUPINE_START_SENSITIVITY=0.35
PORCUPINE_STOP_SENSITIVITY=0.35
```

**If too many missed detections → increase:**
```bash
PORCUPINE_START_SENSITIVITY=0.6
```

**If too many false positives → decrease:**
```bash
PORCUPINE_START_SENSITIVITY=0.3
```

**Asymmetric tuning:**
```bash
PORCUPINE_START_SENSITIVITY=0.6  # More sensitive (fewer misses)
PORCUPINE_STOP_SENSITIVITY=0.3   # Less sensitive (fewer false stops)
```

### CPU Optimization

**If CPU usage >1%:**

1. **Use compressed model:**
   ```python
   porcupine = pvporcupine.create(
       access_key=Config.PORCUPINE_ACCESS_KEY,
       keywords=['computer', 'terminator'],
       model_path='path/to/porcupine_params_compressed.pv'
   )
   ```

2. **Add voice activity detection (VAD):**
   - Only run Porcupine when audio detected
   - Use simple energy threshold
   - Reduces CPU by 50-70%

3. **Adjust frame rate:**
   - Porcupine processes frames at ~10ms intervals
   - Can reduce to 20ms for lower CPU (slight latency increase)

---

## Troubleshooting

### Issue 1: "ImportError: No module named pvporcupine"

**Solution:**
```bash
pip install pvporcupine
```

### Issue 2: "Invalid AccessKey"

**Solution:**
1. Check `.env` has correct key
2. Verify key at https://console.picovoice.ai/
3. Ensure no extra spaces/quotes

### Issue 3: "Platform not supported"

**Solution:**
1. Check Porcupine version: `pip show pvporcupine`
2. Update to latest: `pip install --upgrade pvporcupine`
3. If still fails, contact Picovoice support
4. Fallback to alternative (Precise, Whisper keyword spotting)

### Issue 4: High false positive rate

**Solution:**
1. Lower sensitivity: `0.3` or `0.25`
2. Choose unique wake words (avoid common conversation words)
3. Train custom keywords with distinct phonemes
4. Add confirmation step ("Did you say X?")

### Issue 5: High false negative rate

**Solution:**
1. Increase sensitivity: `0.6` or `0.7`
2. Check microphone input (test with `test_audio.py`)
3. Verify sample rate matches (16 kHz)
4. Reduce background noise
5. Speak louder/clearer

### Issue 6: Device busy / audio conflicts

**Solution:**
```python
# In wake_word.py, add device cleanup
def __init__(self):
    # Kill any existing audio processes
    subprocess.run(['pkill', '-9', 'arecord'], stderr=subprocess.DEVNULL)
    time.sleep(0.2)

    # Then initialize Porcupine
    self.porcupine = pvporcupine.create(...)
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] Porcupine compatibility tested on Jetson
- [ ] AccessKey obtained and stored in `.env`
- [ ] Wake words chosen (built-in or custom)
- [ ] Sensitivity tuned for environment
- [ ] CPU usage <1% when idle
- [ ] Detection accuracy >95% at 2m

### Implementation

- [ ] `src/audio/wake_word.py` created
- [ ] Config updated with Porcupine settings
- [ ] Conversation prototype integrated
- [ ] State management implemented
- [ ] Error handling added
- [ ] Unit tests written

### Testing

- [ ] Manual wake word tests passed
- [ ] False positive rate <1% (5-min conversation)
- [ ] Distance testing passed (90%+ at 2m)
- [ ] Long-term stability (24+ hours no crashes)
- [ ] Memory leak check (no growth over time)

### Production

- [ ] systemd service configured
- [ ] Graceful shutdown handling
- [ ] Monitoring/alerting setup
- [ ] Documentation updated (README, CLAUDE.md)

---

## Next Steps

### Phase 2A: Basic Wake Word (Estimated: 4-6 hours)

1. ✅ Test Porcupine on Jetson → `python test_porcupine.py`
2. ✅ Get AccessKey → https://console.picovoice.ai/
3. Implement `src/audio/wake_word.py` (1-2 hours)
4. Integrate with prototype (1-2 hours)
5. Test and tune (1-2 hours)

### Phase 2B: Dual Wake Word + State Management (Estimated: 3-4 hours)

1. Add STOP keyword detection
2. Implement conversation state machine
3. Add timeout handling (auto-stop after N minutes)
4. Test start/stop flow

### Phase 2C: Always-On Service (Estimated: 4-6 hours)

1. Refactor to background thread/process
2. Create systemd service
3. Test long-term stability
4. Production deployment

---

## References

- **Full Research:** `/mnt/d/GIT/english-companion-nx/MD/PORCUPINE_RESEARCH.md`
- **Porcupine Docs:** https://picovoice.ai/docs/api/porcupine-python/
- **Picovoice Console:** https://console.picovoice.ai/
- **Example Code:** https://github.com/Picovoice/porcupine/tree/master/demo/python

---

**Last Updated:** October 31, 2025
**Status:** Ready for implementation
**Next Action:** Run `python test_porcupine.py` on Jetson
