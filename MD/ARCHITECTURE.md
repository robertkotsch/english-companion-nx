# Architecture Documentation

Detailed architecture, data flow, and performance specifications for English Companion NX.

## System Architecture (Phase 2B)

```
┌─────────────────────────────────────────┐
│  👂 Always-On Wake Word Detection       │
│      (OpenWakeWord, ~1-2% CPU)         │
│   START: "hey jarvis" | STOP: "alexa"  │
└─────────────────────────────────────────┘
                ↓ (START detected)
┌─────────────────────────────────────────┐
│   💬 CONVERSATION SESSION STARTS        │
│      (Greeting generated & spoken)      │
└─────────────────────────────────────────┘
        ↓                            ↑
    Listen for:                      │
    - STOP word ("alexa") ───────────┘ (end session)
    - 30s idle timeout ──────────────┘ (auto-end)
    - User speech ↓
                ↓
┌─────────────────────────────────────────┐
│  🎤 VAD Recording (PyAudio, tmpfs)      │
│   Auto-stops after 3s silence           │
│   (/tmp/companion-audio/recording_*.wav)│
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  🧠 Whisper Small Transcription         │
│    (GPU, in-memory, ~1-2s)              │
│    + Hallucination filter               │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  💬 Conversation Manager (Context)      │
│    Last 20 exchanges in memory          │
│    + System prompt (friendly teacher)   │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  🤖 Qwen2.5 3B Instruct (Ollama, ~5-7s) │
│    localhost:11434 via HTTP             │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  🔊 Coqui VITS TTS Synthesis            │
│    (GPU, in-memory, ~2.5s)              │
│    (/tmp/companion-audio/tts_*.wav)     │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  📢 Audio Output (Anker PowerConf S3)   │
│    PulseAudio via paplay                │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  🔁 Back to Session Listening...        │
│    (for next question or timeout)       │
│    Track last_activity_time             │
└─────────────────────────────────────────┘
                ↓ (session ends)
┌─────────────────────────────────────────┐
│  📊 Session Summary & Evaluation        │
│    Display stats, return to wake word   │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  💤 Back to Wake Word Listening...      │
│    (waiting for "hey jarvis")           │
└─────────────────────────────────────────┘
```

## Data Flow (Conversation Flow - Phase 2B)

### Wake Word Listening (Always-On)

**1. Wake Word Detection Loop**
- OpenWakeWord listens continuously (80ms chunks, 16000 Hz)
- Detects "hey jarvis" with confidence score
- 2-second cooldown prevents duplicates
- Score typically >0.7 for good detection (tested: 0.991!)

### Conversation Session Starts

**2. Session Initialization**
- Stop wake word detector (free audio device)
- Generate greeting with LLM
- Synthesize greeting with TTS
- Play greeting through speaker
- Clear greeting from context (don't confuse conversation)
- Initialize last_activity_time (for idle timeout)

**3. Session Listening Loop**
- Listen for: STOP word ("alexa"), User speech, or Idle timeout (30s)
  - IF STOP WORD → End session, show summary, return to wake word
  - IF IDLE TIMEOUT → End session, show summary, return to wake word
  - IF USER SPEAKS ↓

**4. VAD Recording**
- Stop wake detector (free audio device for recording)
- Open PyAudio stream (reuse 16000 Hz sample rate)
- Play beep (700Hz, 0.3s, 70% volume)
- Record audio continuously (0.1s chunks)
- Calculate energy level per chunk
- Detect silence: energy < 0.01 threshold
- Auto-stop after 3.0s continuous silence
- Save to /tmp/companion-audio/recording_<uuid>.wav
- Min duration: 0.5s, Max duration: 30s (safety)

**5. Transcription & Filtering**
- Transcribe with Whisper small (GPU, FP16, ~1-2s)
- Apply hallucination filter
- Reject: "you", "thank you", "okay", short strings (≤2 chars)
- If hallucination → ignore, DON'T reset idle timer, continue loop
- If valid speech → continue to LLM

**6. Conversation Processing**
- Load conversation context (system prompt + last 20 exchanges)
- Add user message to history
- Send to Ollama (qwen2.5:3b-instruct via HTTP, ~5-7s)
- LLM generates response (streaming disabled)
- Add response to conversation history

**7. Response Synthesis & Playback**
- Synthesize with Coqui VITS (GPU, ~2.5s)
- Save to /tmp/companion-audio/tts_<uuid>.wav
- Play through PulseAudio (paplay to PowerConf S3)
- Delete audio files immediately (no SSD write!)
- Display context summary (exchanges count, memory usage)

**8. Session Continue**
- Restart wake detector (re-enable audio device)
- Update last_activity_time (reset idle timer)
- Increment session exchange count
- Return to step 3 (Session Listening Loop)

### Session Ends (Manual or Timeout)

**9. Session Summary**
- Display total exchanges
- Display session duration
- Show evaluation message based on exchange count:
  - 1-2 exchanges: "Short session"
  - 3-5 exchanges: "Good practice"
  - 6+ exchanges: "Excellent conversation!"
- Restart wake detector
- Return to step 1 (Wake Word Listening)

## Performance Breakdown

### Per Exchange Timing

- Wake word detection: ~80ms per chunk (continuous, ~1-2% CPU)
- VAD recording: Variable (stops 3.0s after speech ends)
  - Short question: ~3-5s
  - Long explanation: ~10-20s
  - Maximum: 30s (safety limit)
- Transcription: ~1-2s (Whisper small on GPU)
- LLM generation: ~5-7s (Ollama qwen2.5:3b-instruct)
- TTS synthesis: ~2.5s (Coqui VITS on GPU)

**Total: ~10-20s per exchange** (varies by speech length)

### Performance Targets

**Latency Goals:**
```
Wake word detection:      <200ms
Audio recording:          ~3-5s (user speech)
Whisper transcription:    <1.5s
LLM generation:           <2s (50 tokens)
TTS synthesis:            <1s
──────────────────────────────
Total (typical):          <5s
Target:                   <3s
```

**Accuracy Goals:**
```
Wake word accuracy:       >95%
Transcription (WER):      <5%
Grammar detection:        >80% precision
User satisfaction:        >85% (subjective)
```

**Reliability Goals:**
```
Uptime:                   >99.5% (24/7)
Memory stability:         No leaks over 7 days
Service restarts:         <1 per month
Mean time to recovery:    <5 minutes
```

## Resource Allocation

### Memory Distribution (16GB Total)

```
System + OS:              3.0 GB  (Linux, services)
Whisper Medium:           2.0 GB  (loaded at startup)
Llama 3.1 13B (q4_0):     8.0 GB  (loaded at startup)
Coqui TTS:                0.5 GB  (loaded at startup)
Python Application:       1.0 GB  (service code)
Audio Buffers:            0.5 GB  (recording/playback)
System Buffer:            1.0 GB  (safety margin)
────────────────────────────────
Total:                   16.0 GB
```

**Tight Allocation - No Room for Errors!**

### SSD Write Budget (Daily)

```
Conversation logs:       50-100 MB  (5-min buffering)
System logs:             50-100 MB  (logrotate)
Model updates (rare):    0-5 GB     (manual only)
Audio saves (optional):  0 MB       (use tmpfs)
────────────────────────────────
Typical Daily Total:     100-200 MB  (0.2% of 50GB limit)
```

**Well Under Limit - But Still Maintain Discipline!**

## Data Formats

### Conversation Log Entry

```json
{
  "timestamp": "2025-10-27T14:30:45.123Z",
  "user": "How do you say 'hello' in English?",
  "assistant": "We say 'hello' or 'hi' for greetings...",
  "metadata": {
    "response_time_ms": 1234,
    "grammar_corrections": [],
    "topic_used": "greetings_vocabulary"
  }
}
```

### Context Window Format

```python
[
  {"role": "user", "content": "How are you?"},
  {"role": "assistant", "content": "I'm doing well, thanks!"},
  {"role": "user", "content": "Tell me about..."}
]
```

### System Prompt

```text
You are a friendly, patient English conversation partner for an adult learner.

Your primary goal is to have genuine, engaging conversations. The user is
practicing English and wants someone to talk to regularly.

Core Behaviors:
- Be genuinely interested in what the user says
- Ask thoughtful follow-up questions
- Share opinions and perspectives (have personality)
- Remember context from previous conversations
- Stay informed about current events (via provided topics)

Language Learning Support:
- Occasionally and gently correct grammar errors (max 1-2 per conversation)
- Introduce new vocabulary naturally in context
- Rephrase complex sentences if the user seems confused
- Prioritize communication over perfect accuracy
- Never interrupt the flow of conversation for corrections

Correction Style:
- Frame positively: "I understood you! We usually say..."
- Integrate naturally into responses
- Focus on clear, teachable errors only

Topics:
- You have access to curated trending topics
- Bring these up naturally when conversation lags
- Connect topics to user's interests when possible

Remember: You're a companion first, teacher second.
```

## Data Storage Strategy

### Phase 1-3 (Minimal - JSONL)

```python
# Simple JSONL append-only log
# /mnt/nvme/companion/conversations.jsonl

{"timestamp": "2025-10-27T14:30:45.123Z",
 "user": "How do you say hello?",
 "assistant": "We say 'hello' or 'hi'...",
 "metadata": {"response_time_ms": 1234}}
```

**Advantages:**
- ✅ Zero infrastructure (no DB to manage)
- ✅ Minimal SSD writes (buffered)
- ✅ Human-readable for debugging
- ✅ Easy backup/archive (just copy file)
- ✅ Simple to parse for analysis

**Load last N conversations:**
```python
def load_context(n=20):
    with open(CONVERSATION_LOG) as f:
        lines = f.readlines()
        return [json.loads(line) for line in lines[-n:]]
```

### Phase 4+ (Optional - SQLite)

```sql
-- /mnt/nvme/companion/conversations.db

CREATE TABLE conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    user_message TEXT NOT NULL,
    assistant_message TEXT NOT NULL,
    response_time_ms INTEGER,
    grammar_corrections TEXT,  -- JSON array
    topic TEXT,
    sentiment TEXT
);

-- Still use buffered batch inserts!
-- Don't write on every conversation
```

## Network & Deployment

### Jetson Network

- IP: `192.168.x.x` (configure in your network)
- Service port: 8000 (if using API mode)
- Metrics port: 8001 (Prometheus)
- Path: `~/apps/english-companion-nx`

### Git-Based Deployment Workflow

```
Dev Machine → git push → GitHub → git pull → Jetson
```

**Principle:** Git is single source of truth. Jetson is read-only from GitHub.

See `MD/git-deployment-workflow.md` for complete deployment guide.

---

**Last Updated:** December 2024
