# Voice Assistant Usage Guide

## Phase 2B: Always-On Voice Assistant with Conversation Sessions

The voice assistant combines wake word detection with conversation sessions for natural, hands-free conversations. Start a session with a wake word, have multiple Q&A exchanges, then end the session with a stop trigger word.

## Quick Start

```bash
cd ~/apps/english-companion-nx
source .venv/bin/activate
python voice_assistant.py
```

**Then:**
1. Say `"hey jarvis"` to **start a conversation session**
2. Ask multiple questions without repeating the wake word
3. Say `"alexa"` to **end the session** when you're done

## Conversation Sessions

### Traditional vs Session Mode

**Traditional (single Q&A):**
```
"hey jarvis" → Question → Answer → "hey jarvis" → Question → Answer...
```

**Session Mode (multiple Q&A):**
```
"hey jarvis" → SESSION STARTS
  → Question 1 → Answer 1
  → Question 2 → Answer 2
  → Question 3 → Answer 3
  → "alexa" → SESSION ENDS
```

### Benefits

- ✅ **Natural:** Multiple questions without repeating wake word
- ✅ **Efficient:** Saves 2+ seconds per follow-up question
- ✅ **Context:** Maintains conversation context across exchanges
- ✅ **Flexible:** Quick 1-question or extended multi-question sessions

See `CONVERSATION_SESSION_MODE.md` for detailed documentation.

## How It Works

```
┌─────────────────────────────────────────┐
│   👂 Wake Word Detection (Always On)    │
│        Listening for "hey jarvis"       │
└─────────────────────────────────────────┘
                ↓ detected
┌─────────────────────────────────────────┐
│   💬 CONVERSATION SESSION STARTS        │
└─────────────────────────────────────────┘
        ↓                            ↑
    Listen for:                      │
    - Stop word ("alexa") ───────────┘ (end session)
    - Or user speech ↓
                ↓
┌─────────────────────────────────────────┐
│   🎤 Record User Speech (VAD-based)     │
│    Stops after 3s of silence            │
│      (saved to /tmp/companion-audio)    │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│   🧠 Whisper Transcription (GPU, ~1-2s) │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│    💬 Ollama LLM Response (~5-7s)       │
│    (qwen2.5:3b-instruct)                │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│    🔊 TTS Synthesis (GPU, ~2.5s)        │
│        (Coqui VITS)                     │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│      📢 Play Response (Speaker)         │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  🔁 Back to Session Listening...        │
│     (for next question or stop word)    │
└─────────────────────────────────────────┘
```

## Performance

**Expected timing per conversation:**
- Wake word detection: ~80ms (continuous, low CPU)
- Recording: Variable (stops 1.5s after you stop speaking)
  - Short question: ~3-5s
  - Long explanation: ~10-20s
  - Maximum: 30s (safety limit)
- Transcription: ~1-2s (Whisper small on GPU)
- LLM response: ~5-7s (Ollama qwen2.5:3b-instruct)
- TTS synthesis: ~2.5s (Coqui VITS on GPU)
- **Total: ~10-20s** from wake word to response (varies by question length)

## Usage

### Basic Usage

```bash
python voice_assistant.py
```

**Default settings:**
- Wake word: "hey jarvis"
- Threshold: 0.5
- Audio device: 0 (PowerConf S3)

### Custom Settings

```bash
# Use different wake word
python voice_assistant.py alexa

# Adjust detection threshold (higher = more strict)
python voice_assistant.py hey_jarvis 0.7

# Use different audio device
python voice_assistant.py hey_jarvis 0.5 1
```

### Available Wake Words

Built-in OpenWakeWord models:
- `hey_jarvis` (recommended)
- `alexa`
- `hey_mycroft`
- `timer`

## Example Session

```
🚀 English Companion NX - Voice Assistant (Phase 2B)
============================================================
🖥️  Device: CUDA
   GPU: NVIDIA Orin NX

👂 Initializing wake word detection...
🎤 Wake word detector initialized (OpenWakeWord)
   START model: 'hey_jarvis' (threshold: 0.5)
   Available models: ['alexa', 'hey_mycroft', 'hey_jarvis', 'timer']

✅ All systems ready!
============================================================

👂 ALWAYS-ON VOICE ASSISTANT
============================================================
Wake word: 'hey jarvis'
Say the wake word to start a conversation
Press Ctrl+C to exit
============================================================

🎧 Listening for wake word...

🎯 WAKE WORD DETECTED! (score: 0.991)

============================================================
🎯 WAKE WORD DETECTED! (Conversation #1)
============================================================

🔔 Beep!
🎤 Recording... (speak now)
🧠 Transcribing...
👤 You: How do you say hello in English?
💭 Thinking...
✅ Response generated (7.2s)
🔊 Synthesizing speech...
🤖 Assistant: Great question! In English, we have several ways to greet people...

📊 Context: 1 exchanges in memory
💾 Memory: 45.2% used (7.2GB / 16.0GB)
⏱️  Total: 14.3s

============================================================
🎧 Returning to wake word listening...
============================================================

🎧 Listening for wake word...

[Say "hey jarvis" again for another conversation...]
```

## Differences from `conversation_prototype.py`

| Feature | conversation_prototype.py | voice_assistant.py |
|---------|---------------------------|-------------------|
| **Trigger** | Press Enter | Say "hey jarvis" |
| **Mode** | Interactive (manual) | Always-on (hands-free) |
| **Wake Word** | No | Yes (OpenWakeWord) |
| **Use Case** | Testing/debugging | Production 24/7 use |
| **CPU Usage** | 0% when idle | ~1-2% for wake word detection |

## Tips for Best Results

### Wake Word Detection

1. **Speak clearly**: Enunciate "hey jarvis" naturally
2. **Optimal distance**: 0.5-1.5 meters from microphone
3. **Reduce background noise**: Better signal-to-noise ratio
4. **Wait for beep**: Start speaking after the beep sound
5. **Detection score**: Aim for >0.7 (shown in logs)

### Voice Activity Detection (VAD)

The system uses intelligent silence detection to automatically stop recording:

**How it works:**
1. After wake word, beep signals you can start speaking
2. System detects when you start talking (audio level > threshold)
3. Records continuously while you speak
4. Waits for 3.0 seconds of silence
5. Automatically stops recording and processes your question

**Default settings:**
- Silence threshold: 0.01 (audio level)
- Silence duration: 3.0s
- Minimum recording: 0.5s
- Maximum recording: 30s (safety limit)

**Adjusting VAD sensitivity:**

Edit `voice_assistant.py` and modify the `record_with_vad()` parameters:

```python
audio_file = self.recorder.record_with_vad(
    silence_threshold=0.01,   # Lower = more sensitive (e.g., 0.005)
    silence_duration=3.0,     # Longer = more patient (e.g., 4.0)
    min_duration=0.5,         # Minimum recording time
    max_duration=30.0         # Maximum recording time
)
```

**If recording stops too early:**
- Increase `silence_duration` to 4.0 or 5.0 seconds
- Speak more continuously without long pauses

**If recording doesn't stop:**
- Lower `silence_threshold` to 0.005 (more sensitive to silence)
- Ensure quiet environment with less background noise

**Test VAD separately:**
```bash
python tests/test_vad_recording.py           # Default: 0.01 threshold, 3.0s silence
python tests/test_vad_recording.py 0.02      # Less sensitive (noisy environment)
python tests/test_vad_recording.py 0.01 5.0  # Wait 5s of silence (very patient)
```

### Audio Quality

- **Microphone position**: Face the PowerConf S3 speaker
- **Volume**: Speak at normal conversation volume
- **Environment**: Quiet room works best
- **Accent**: Model trained on English, works with non-native speakers (tested at 0.991 confidence!)

### Performance Optimization

- **GPU**: Ensure CUDA is enabled for Whisper and TTS
- **Memory**: Monitor with `jtop` during operation
- **Temperature**: Keep Jetson cool (<70°C) for consistent performance

## Troubleshooting

### Wake word not detecting

```bash
# Test wake word detection separately
python tests/test_wake_word.py basic 30

# Debug with real-time confidence scores
python debug_wake_word.py 30 hey_jarvis 0
```

**Common issues:**
- Audio level too low (check `alsamixer`)
- Wrong microphone device (verify with `test_audio.py`)
- Background noise too high
- Threshold too strict (try 0.3 instead of 0.5)

### Multiple detections for one wake word

This should be fixed with the 2-second cooldown. If still occurring:
- Check `src/audio/wake_word.py` line 137: `self.cooldown_seconds = 2.0`
- Increase cooldown to 3.0 if needed

### "Device or resource busy" error

```bash
# Kill any orphan audio processes
pkill -9 arecord

# Restart the assistant
python voice_assistant.py
```

### Memory issues

```bash
# Check available memory
free -h

# Monitor during operation
jtop

# If memory critical, restart service
# (Models will be reloaded)
```

## Systemd Service (Future: Phase 2C)

To run the voice assistant as a 24/7 service:

```bash
# Create systemd service
sudo nano /etc/systemd/system/english-companion-nx.service

# Enable and start
sudo systemctl enable english-companion-nx
sudo systemctl start english-companion-nx

# Check status
sudo systemctl status english-companion-nx

# View logs
journalctl -u english-companion-nx -f
```

**Note:** Service configuration will be added in Phase 2C.

## Memory Management

The voice assistant uses buffered logging and automatic cleanup:

- **Conversation logs**: Flushed every 5 minutes (not after each conversation)
- **Audio temp files**: Saved to `/tmp` (RAM disk), deleted immediately
- **Memory cleanup**: Every 10 conversations
- **Context pruning**: Last 20 exchanges kept in memory

## Development

### Testing Components Separately

```bash
# Test wake word only
python tests/test_wake_word.py basic 30

# Test conversation only (no wake word)
python conversation_prototype.py

# Test full voice assistant
python voice_assistant.py
```

### Monitoring Performance

```bash
# GPU utilization
watch -n 1 nvidia-smi

# Memory usage
watch -n 1 free -h

# Temperature
watch -n 1 cat /sys/class/thermal/thermal_zone*/temp

# All-in-one Jetson stats
jtop
```

## Next Steps

**Phase 2B Complete ✅**

**Coming in Phase 2C:**
- Systemd service configuration
- Automatic startup on boot
- Log rotation
- Health monitoring
- Auto-restart on failure

**Coming in Phase 3:**
- MCP topic integration
- Current events awareness
- Grammar correction feedback
- Multi-turn conversation context

## Support

- Documentation: See `CLAUDE.md` for development guidelines
- Installation: See `INSTALLATION.md` for setup instructions
- Hardware: See `MD/JETSON_SETUP.md` for Jetson configuration
- Issues: Check `debug_wake_word.py` for diagnostics

---

**Status:** Phase 2B - Always-On Voice Assistant (Working!)
**Last Updated:** December 2024
**Tested On:** Jetson Orin NX 16GB with Anker PowerConf S3
