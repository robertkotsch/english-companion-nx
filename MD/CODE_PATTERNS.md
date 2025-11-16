# Code Patterns & Development Guidelines

Best practices and code patterns for developing English Companion NX.

## SSD Protection (ABSOLUTE RULES)

### ✅ DO

- Buffer conversation logs (5-min flush intervals)
- Use `/tmp` (tmpfs) for all audio temp files
- Keep models in RAM (load once at startup)
- Batch database writes if using SQLite
- Compress old logs automatically

### ❌ NEVER

- Save every audio recording to SSD
- Write logs on every conversation
- Reload models during operation
- Enable unnecessary file logging
- Use SSD for scratch/temp data

## Memory Safety

### ✅ DO

- Load all models at service startup
- Prune conversation context (keep last 10-20 exchanges)
- Run garbage collection periodically (every 10 conversations)
- Clear CUDA cache after GPU operations
- Monitor memory with MemoryGuard

### ❌ NEVER

- Keep unlimited conversation history in memory
- Load models on-demand (defeats caching)
- Ignore memory warnings
- Run without MemoryMax systemd limits
- Accumulate audio buffers

## Core Code Patterns

### Model Loading (Singleton Pattern)

```python
# GOOD: Load once, reuse forever
class VoiceAssistant:
    def __init__(self):
        # Load models at startup - keep in RAM forever
        self.wake_detector = WakeWordDetector(...)  # OpenWakeWord
        self.transcription = TranscriptionService()  # Whisper small
        self.synthesis = SynthesisService()          # Coqui VITS
        self.conversation = ConversationManager()    # Context manager

        # All models stay in RAM until service restarts
        # NEVER reload during operation!
```

```python
# BAD: Loading models on-demand (defeats caching!)
def transcribe(audio_file):
    model = whisper.load_model("small")  # ❌ NEVER DO THIS
    return model.transcribe(audio_file)
```

### Audio Device Management (Critical Pattern)

```python
# GOOD: Stop/start wake detector to free audio device
def run_conversation_session(self):
    while True:
        result = self.wake_detector.detect_once(timeout=2.0)

        if result == WakeWordType.NONE:  # User wants to speak
            # CRITICAL: Stop wake detector before VAD recording
            # This frees the audio device for recording
            self.wake_detector.stop()

            # Now VAD recording can open the audio device
            success = self.handle_conversation()

            # CRITICAL: Restart wake detector after recording
            # Resume wake word detection
            self.wake_detector.start()
```

**Why this matters:** Audio device can only be accessed by one process at a time. Wake word detector keeps the device open for continuous listening. Must stop it before VAD recording can access the device.

### Sample Rate Reuse (Optimization)

```python
# GOOD: Detect once, reuse everywhere
def __init__(self):
    # Wake detector finds working sample rate at init
    self.wake_detector = WakeWordDetector(audio_device_index=0)

    # Store detected rate (e.g., 16000 Hz for PowerConf S3)
    self.detected_sample_rate = self.wake_detector.device_sample_rate

    # Reuse in VAD recording (no re-probing!)
    # This avoids ALSA warnings and speeds up initialization
    audio_file = self.recorder.record_with_vad(
        sample_rate=self.detected_sample_rate,  # Pass known rate
        device_index=0
    )
```

```python
# BAD: Re-probing sample rate every time
def record():
    # This triggers ALSA warnings and wastes time
    for rate in [16000, 48000, 44100]:  # ❌ Don't do this repeatedly
        try:
            # Test rate...
```

### Whisper Hallucination Filtering

```python
# GOOD: Filter false positives during silence
def _is_whisper_hallucination(self, text: str) -> bool:
    """Detect common Whisper hallucinations during silence."""
    normalized = text.lower().strip().strip('.,!?;:')

    # Common silence artifacts that Whisper outputs
    hallucinations = {
        'you', 'thank you', 'thanks', 'okay', 'ok',
        'yeah', 'yes', 'no', 'um', 'uh', 'hmm', 'ah', ''
    }

    # Very short transcriptions are likely noise
    if len(normalized) <= 2:
        return True

    return normalized in hallucinations

# Usage in conversation loop
if not user_message or self._is_whisper_hallucination(user_message):
    if user_message:
        print(f"⚠️  Detected hallucination: '{user_message}' (ignoring)")
    return False  # DON'T reset idle timer for hallucinations
```

**Why this matters:** Whisper often outputs "you" or "thank you" during silence. Without filtering, these would:
1. Reset the idle timeout (preventing session from ending)
2. Send garbage to the LLM (wasting time/resources)
3. Confuse the conversation flow

### Session Idle Timeout Pattern

```python
# GOOD: Track activity, auto-end sessions
def run_conversation_session(self, idle_timeout: float = 30.0):
    last_activity_time = time.time()
    session_count = 0
    session_start_time = time.time()

    while True:
        # Check for idle timeout
        idle_duration = time.time() - last_activity_time

        if idle_duration >= idle_timeout:
            print(f"\n💤 IDLE TIMEOUT ({idle_timeout}s)")
            self._show_session_summary(session_count, session_start_time, idle=True)
            break

        # ... handle conversation ...

        if success:  # Valid conversation exchange (not hallucination!)
            last_activity_time = time.time()  # Reset timer ONLY on valid speech
            session_count += 1
```

**Key points:**
- Reset timer ONLY on successful, valid conversation exchanges
- Don't reset on hallucinations (would prevent timeout)
- Track session start time for summary statistics

### Audio Recording (tmpfs Pattern)

```python
# GOOD: Record to RAM, delete immediately
TEMP_DIR = '/tmp/companion-audio'
temp_file = os.path.join(TEMP_DIR, f'recording_{uuid4()}.wav')

# Record with VAD (auto-stops after silence)
audio_file = recorder.record_with_vad(
    silence_threshold=0.01,
    silence_duration=3.0,
    sample_rate=16000,  # Reuse known rate
    device_index=0
)

# Transcribe
transcript = whisper.transcribe(audio_file)

# Delete immediately - no SSD write!
os.remove(audio_file)
```

```python
# BAD: Saving to SSD
audio_file = os.path.join("~/companion-data/audio", f"recording_{uuid4()}.wav")  # ❌
# This writes to SSD unnecessarily - will wear it out!
```

**Why tmpfs:**
- tmpfs is in RAM (no SSD writes)
- Files automatically cleaned on reboot
- Fast access (RAM speed)
- No SSD wear

### Greeting with Error Handling

```python
# GOOD: Always display greeting, handle errors separately
def greet_user(self):
    greeting = None

    # Generation phase - always completes
    try:
        greeting = self.conversation.generate_response(greeting_prompt)
        if not greeting:
            greeting = "Hey! I'm ready to chat!"
        print(f"🤖 Assistant: {greeting}")
    except Exception as e:
        print(f"⚠️  Greeting generation failed: {e}")
        greeting = "Hey! I'm ready to chat!"
        print(f"🤖 Assistant: {greeting}")

    # Synthesis phase - separate error handling
    # User always sees greeting text even if TTS fails
    try:
        tts_file = self.synthesis.synthesize(greeting)
        self.player.play(tts_file)
        self.synthesis.cleanup_file(tts_file)
    except Exception as e:
        print(f"⚠️  TTS/playback failed: {e}")
        # Greeting already displayed, continue anyway

    # Cleanup in finally block
    finally:
        # Remove greeting from context (don't confuse conversation)
        # Greeting is just welcome message, not part of conversation
        if len(self.conversation.context) >= 2:
            self.conversation.context = self.conversation.context[:-2]
```

**Why this pattern:**
- User always sees greeting (good UX)
- TTS failure doesn't block session start
- Greeting removed from context (doesn't confuse conversation)
- Separate error handling for generation vs. synthesis

### Conversation Logging (Buffered - Planned)

```python
# GOOD: Buffer writes, flush periodically
class ConversationLogger:
    def __init__(self, flush_interval=300):
        self.buffer = []
        self.flush_interval = flush_interval
        self.last_flush = time.time()

    def log(self, user_msg, assistant_msg):
        self.buffer.append({
            'timestamp': datetime.now().isoformat(),
            'user': user_msg,
            'assistant': assistant_msg
        })

        # Auto-flush every 5 minutes
        if time.time() - self.last_flush > self.flush_interval:
            self.flush()  # Single write operation

    def flush(self):
        if not self.buffer:
            return

        # Write all buffered entries at once (single SSD write)
        with open(self.log_file, 'a') as f:
            for entry in self.buffer:
                f.write(json.dumps(entry) + '\n')

        self.buffer = []
        self.last_flush = time.time()
```

```python
# BAD: Writing on every conversation
def log(self, user_msg, assistant_msg):
    with open(self.log_file, 'a') as f:  # ❌ SSD write every time!
        f.write(json.dumps({'user': user_msg, 'assistant': assistant_msg}) + '\n')
```

### Memory Cleanup (Periodic Pattern)

```python
# GOOD: Clean up after every 10 conversations
def handle_conversation(self):
    # ... conversation logic ...

    self.total_count += 1

    # Periodic cleanup (every 10 conversations)
    if self.total_count % 10 == 0:
        gc.collect()                    # Python garbage collection
        torch.cuda.empty_cache()        # Clear GPU cache
        self.memory_monitor.check_memory()  # Log memory usage

        print(f"🧹 Memory cleanup (conversation #{self.total_count})")
```

### Context Pruning Pattern

```python
# GOOD: Keep only last N exchanges
class ConversationManager:
    def __init__(self, max_context_size=20):
        self.max_context_size = max_context_size
        self.context = []

    def add_exchange(self, user_msg, assistant_msg):
        self.context.append({"role": "user", "content": user_msg})
        self.context.append({"role": "assistant", "content": assistant_msg})

        # Prune to last N exchanges (N*2 messages)
        max_messages = self.max_context_size * 2
        if len(self.context) > max_messages:
            # Keep system prompt (first message) + last N exchanges
            self.context = [self.context[0]] + self.context[-max_messages:]
```

```python
# BAD: Unbounded context growth
def add_exchange(self, user_msg, assistant_msg):
    self.context.append({"role": "user", "content": user_msg})
    self.context.append({"role": "assistant", "content": assistant_msg})
    # ❌ Context keeps growing, will OOM eventually!
```

## Configuration Pattern

### Environment Variables with Defaults

```python
# GOOD: Use environment variables with sensible defaults
import os
from pathlib import Path

class Config:
    # Audio settings
    AUDIO_TEMP_DIR = Path(os.getenv('AUDIO_TEMP_DIR', '/tmp/companion-audio'))
    AUDIO_SAMPLE_RATE = int(os.getenv('AUDIO_SAMPLE_RATE', '16000'))

    # Model settings
    WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'small')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'qwen2.5:3b-instruct')
    OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'localhost:11434')

    # Memory settings
    MEMORY_WARNING_THRESHOLD = float(os.getenv('MEMORY_WARNING_THRESHOLD', '0.85'))
    CONVERSATION_CONTEXT_SIZE = int(os.getenv('CONVERSATION_CONTEXT_SIZE', '20'))

    # Session settings
    IDLE_TIMEOUT = float(os.getenv('IDLE_TIMEOUT', '30.0'))
    SILENCE_THRESHOLD = float(os.getenv('SILENCE_THRESHOLD', '0.01'))
    SILENCE_DURATION = float(os.getenv('SILENCE_DURATION', '3.0'))

    @classmethod
    def ensure_directories(cls):
        """Create required directories if they don't exist."""
        cls.AUDIO_TEMP_DIR.mkdir(parents=True, exist_ok=True)
```

## Error Handling Patterns

### Graceful Degradation

```python
# GOOD: Continue operation even if non-critical components fail
def initialize(self):
    # Critical components - fail fast
    self.wake_detector = WakeWordDetector()  # Must work
    self.transcription = TranscriptionService()  # Must work

    # Optional components - graceful degradation
    try:
        self.metrics_server = PrometheusServer(port=8001)
        self.metrics_server.start()
    except Exception as e:
        print(f"⚠️  Metrics server failed to start: {e}")
        print("Continuing without metrics...")
        self.metrics_server = None
```

### Retry with Exponential Backoff

```python
# GOOD: Retry transient failures (network, LLM)
def generate_response(self, prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = self.llm_client.generate(prompt)
            return response
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                print(f"⚠️  LLM request failed (attempt {attempt+1}), retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"❌ LLM request failed after {max_retries} attempts")
                return "I'm having trouble thinking right now. Can you try again?"
```

## Testing Patterns

### Component Testing

```python
# Test individual components in isolation
def test_whisper_transcription():
    service = TranscriptionService()
    result = service.transcribe("test_audio.wav")
    assert result is not None
    assert len(result) > 0

def test_hallucination_filter():
    assistant = VoiceAssistant()
    assert assistant._is_whisper_hallucination("you")
    assert assistant._is_whisper_hallucination("thank you")
    assert not assistant._is_whisper_hallucination("hello world")
```

### Integration Testing

```python
# Test full conversation flow
def test_conversation_flow():
    assistant = VoiceAssistant()

    # Simulate conversation
    user_message = "How are you?"
    response = assistant.conversation.generate_response(user_message)

    assert response is not None
    assert len(response) > 0
    assert len(assistant.conversation.context) == 2  # User + assistant
```

## Documentation Patterns

### Inline Documentation

```python
def record_with_vad(
    self,
    silence_threshold: float = 0.01,
    silence_duration: float = 3.0,
    max_duration: float = 30.0,
    sample_rate: int = 16000,
    device_index: int = 0
) -> Optional[str]:
    """
    Record audio with Voice Activity Detection (VAD).

    Automatically stops recording after detecting continuous silence.

    Args:
        silence_threshold: Energy threshold below which is considered silence (0.01)
        silence_duration: Seconds of silence before stopping (3.0s)
        max_duration: Maximum recording duration as safety limit (30.0s)
        sample_rate: Audio sample rate in Hz (16000 for PowerConf S3)
        device_index: PyAudio device index (0 for default)

    Returns:
        Path to recorded WAV file in tmpfs, or None if recording failed

    Note:
        - Audio saved to /tmp/companion-audio/ (tmpfs, no SSD writes)
        - Caller responsible for deleting file after use
        - Plays beep before recording starts
    """
```

### File Headers

```python
"""
Audio recorder with Voice Activity Detection (VAD).

This module provides VAD-based recording that automatically stops after
detecting continuous silence. All recordings are saved to tmpfs to avoid
SSD writes.

Key features:
- Energy-based silence detection
- Configurable silence threshold and duration
- Auto-cleanup of orphaned processes
- Beep generation for user feedback
- Sample rate reuse from wake word detector

Usage:
    recorder = AudioRecorder()
    audio_file = recorder.record_with_vad(
        silence_threshold=0.01,
        silence_duration=3.0
    )
    # ... use audio_file ...
    os.remove(audio_file)  # Clean up

See: voice_assistant.py for integration example
"""
```

---

**Last Updated:** December 2024
