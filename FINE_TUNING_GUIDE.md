# Fine-Tuning Guide - English Companion NX

## Overview

This guide helps you optimize the voice assistant for your personal English conversation practice needs. The system is designed to be highly configurable - adjust these settings to match your speaking style, environment, and learning preferences.

## Current Status (Phase 2B Complete)

### ✅ Working Features
- Wake word detection ("hey jarvis")
- Voice Activity Detection (auto-stops after silence)
- Conversation sessions (multiple Q&A exchanges)
- Spoken greeting when session starts
- 30-second idle timeout with session summary
- Whisper hallucination filtering
- Context management (conversation history)
- Session evaluation and statistics

### ⏭️ Features to Skip
- **Stop trigger ("alexa")** - Not yet working, but not needed
  - Reason: Idle timeout handles session ending gracefully
  - Alternative: Let session timeout after 30s of inactivity
  - Future: Can be implemented if requested

---

## 1. Timing & Thresholds

### 1.1 VAD Silence Duration

**Current:** 3.0 seconds
**Location:** `voice_assistant.py` line 125

```python
silence_duration=3.0,  # Stop after 3.0s of silence
```

**When to adjust:**
- **Too short (cuts you off):** Increase to 4.0-5.0s if you need more thinking pauses
- **Too long (slow response):** Decrease to 2.0-2.5s if you speak quickly without pauses

**How to change:**
```python
# Edit voice_assistant.py, line 125
silence_duration=4.0,  # Give yourself more time to think
```

### 1.2 Idle Timeout

**Current:** 30.0 seconds
**Location:** `voice_assistant.py` line 278 (parameter default)

```python
def run_conversation_session(self, idle_timeout: float = 30.0):
```

**When to adjust:**
- **Too short:** Increase to 60.0s if you need more time between questions
- **Too long:** Decrease to 15.0s for quicker auto-logout

**How to change:**
```python
# Edit voice_assistant.py, line 278
def run_conversation_session(self, idle_timeout: float = 60.0):
```

### 1.3 Wake Word Detection Threshold

**Current:** 0.5 (50% confidence)
**Location:** Command line argument or `voice_assistant.py` line 316-317

**When to adjust:**
- **False positives:** Increase to 0.6-0.7 (more strict)
- **Missed detections:** Decrease to 0.3-0.4 (more sensitive)

**How to change:**
```bash
# Via command line
python voice_assistant.py hey_jarvis alexa 0.6 0.5 0

# Or edit voice_assistant.py, line 316
wake_threshold = 0.6  # More strict
```

### 1.4 Wake Word Detection Cooldown

**Current:** 2.0 seconds
**Location:** `src/audio/wake_word.py` line 137

```python
self.cooldown_seconds = 2.0  # Ignore detections within this window
```

**When to adjust:**
- **Duplicate detections:** Increase to 3.0-4.0s
- **Slow to respond:** Decrease to 1.0-1.5s

---

## 2. Conversation Quality

### 2.1 System Prompt (Persona & Teaching Style)

**Current:** Friendly English conversation partner
**Location:** `src/conversation/manager.py` (system prompt)

**Example customizations:**

**More Grammar-Focused:**
```python
system_prompt = """You are a professional English teacher helping an adult learner.

Focus on:
- Correct grammar mistakes gently but consistently
- Explain grammar rules briefly when correcting
- Suggest better phrasing and vocabulary
- Encourage natural conversation while teaching
"""
```

**More Conversational (Less Teaching):**
```python
system_prompt = """You are a friendly native English speaker having casual conversations.

Focus on:
- Natural, flowing dialogue
- Rarely correct mistakes (only if critical)
- Share stories and opinions
- Ask engaging questions
- Be authentic and personable
"""
```

**Professional/Business English:**
```python
system_prompt = """You are a business English conversation partner.

Focus on:
- Professional vocabulary and expressions
- Formal conversation patterns
- Business topics (meetings, emails, presentations)
- Professional etiquette in English
"""
```

### 2.2 Greeting Customization

**Current:** LLM-generated, varies each time
**Location:** `voice_assistant.py` line 238

```python
greeting_prompt = "Greet me briefly and enthusiastically to start our conversation. Keep it very short (1-2 sentences max)."
```

**Example customizations:**

**Add your name:**
```python
greeting_prompt = "Greet Rob briefly and enthusiastically. Keep it very short (1-2 sentences max)."
```

**Specific tone:**
```python
# Casual/friendly
greeting_prompt = "Say a casual, friendly hello to start our chat. Very brief, like talking to a friend."

# Professional
greeting_prompt = "Greet me professionally but warmly, as if starting a business meeting."

# Encouraging/motivational
greeting_prompt = "Give an encouraging greeting to motivate me for English practice. Very brief."
```

**Fixed greeting (no LLM generation):**
```python
# Replace greeting generation with:
greeting = "Hey Rob! Ready to practice some English?"
```

### 2.3 Context Window Size

**Current:** Last 20 exchanges
**Location:** `src/conversation/manager.py`

**When to adjust:**
- **Long conversations:** Increase to 30-50 exchanges
- **Memory issues:** Decrease to 10-15 exchanges
- **Fresh context:** Decrease to 5-10 exchanges

### 2.4 Response Length

**Add to system prompt:**
```python
"Keep responses brief - 2-3 sentences maximum, unless explaining something complex."
```

Or for longer responses:
```python
"Provide detailed, thorough responses with examples. Take your time explaining concepts."
```

---

## 3. Audio Settings

### 3.1 Microphone Sensitivity (VAD Threshold)

**Current:** 0.01 (audio level threshold)
**Location:** `voice_assistant.py` line 124

```python
silence_threshold=0.01,  # Audio level below this = silence
```

**When to adjust:**
- **Noisy environment:** Increase to 0.02-0.03 (less sensitive to background noise)
- **Quiet environment:** Decrease to 0.005-0.008 (more sensitive)

### 3.2 Audio Device Selection

**Current:** Device 0 (PowerConf S3)
**Location:** `voice_assistant.py` line 129, line 74

**To use different microphone:**
```bash
# List available devices
python test_audio.py

# Use device 1 instead
python voice_assistant.py hey_jarvis alexa 0.5 0.5 1
```

### 3.3 Sample Rate

**Current:** Auto-detected (16000 Hz for PowerConf S3)
**Location:** Automatically detected by wake word system

**Usually auto-detection works best.** Only change if you have audio quality issues.

### 3.4 TTS Voice Settings

**Current:** Coqui VITS default voice
**Location:** `src/speech/synthesis.py`

**Future enhancement:** Add parameters for:
- Speaking rate (speed)
- Pitch adjustment
- Voice selection (different voices)

---

## 4. Features to Add

### 4.1 Custom Wake Words (Priority: Medium)

**Current:** Limited to built-in models (hey_jarvis, alexa, hey_mycroft, timer)

**To add custom wake words:**
1. Train custom OpenWakeWord model with your phrase
2. Save .tflite model file
3. Pass custom model path to `WakeWordDetector`

**Example use cases:**
- Your own name: "Hey Rob"
- Custom phrase: "Start conversation"
- Language-specific: "Hola" for Spanish practice

### 4.2 Grammar Correction Feedback (Priority: High)

**Not yet implemented**

**Planned feature:**
- Collect grammar mistakes during session
- Summarize corrections at end of session
- Speak corrections or display them
- Optional grammar practice exercises

**Example implementation:**
```python
def end_session_with_feedback(self):
    """Show grammar corrections from this session"""
    if self.grammar_corrections:
        print("\n📝 Grammar Feedback:")
        for correction in self.grammar_corrections:
            print(f"  - You said: '{correction['original']}'")
            print(f"    Better: '{correction['corrected']}'")
            print(f"    Tip: {correction['explanation']}")
```

### 4.3 Session Persistence (Priority: Low)

**Not yet implemented**

**Planned feature:**
- Save conversation context between sessions
- Resume previous conversation: "Continue where we left off"
- Session history browser

### 4.4 Progress Tracking (Priority: Medium)

**Not yet implemented**

**Planned feature:**
- Track vocabulary introduced over time
- Grammar mistake patterns
- Conversation topics covered
- Speaking time statistics
- Improvement metrics

**Example metrics:**
- Average conversation length (growing over time)
- New words learned per week
- Grammar accuracy trends
- Topics practiced

### 4.5 User Profile & Preferences (Priority: Low)

**Not yet implemented**

**Planned feature:**
- Save your name, preferences, learning goals
- Personalized greetings
- Adaptive difficulty (vocabulary level)
- Topic preferences

### 4.6 Topic Suggestions (Priority: Medium)

**Not yet implemented**

**Planned feature:**
- Suggest conversation topics when idle
- Daily conversation starters
- Themed practice sessions (travel, food, business, etc.)
- News-based conversations

### 4.7 Multi-Session Analytics (Priority: Low)

**Not yet implemented**

**Planned feature:**
- Weekly/monthly practice summaries
- Conversation heatmap (when you practice most)
- Streak tracking (consecutive days)
- Achievement system

---

## 5. Performance Optimization

### 5.1 Model Sizes

**Current:**
- Whisper: `small` (faster, good accuracy)
- LLM: `llama3.2:3b` (fast, 16GB RAM compatible)
- TTS: Coqui VITS (high quality)

**Optimization options:**

**Faster (lower quality):**
```python
# Whisper tiny (fastest, less accurate)
WHISPER_MODEL=tiny

# Smaller LLM
OLLAMA_MODEL=llama3.2:1b
```

**Better quality (slower):**
```python
# Whisper medium (more accurate, slower)
WHISPER_MODEL=medium

# Larger LLM (better responses)
OLLAMA_MODEL=llama3.1:8b
```

### 5.2 Response Time Improvements

**Current timing:**
- Recording: Variable (VAD-based)
- Transcription: ~1-2s (Whisper small on GPU)
- LLM response: ~6-8s (llama3.2:3b)
- TTS synthesis: ~2.5s (Coqui VITS on GPU)
- **Total: ~10-20s per exchange**

**To improve:**
1. **Use smaller models** (see 5.1)
2. **Optimize Ollama:** Pre-load model, increase context cache
3. **Parallel processing:** Generate TTS while LLM is thinking (future)
4. **Streaming:** Start speaking response as it's generated (future)

### 5.3 Memory Usage Reduction

**Current:** ~8-9GB RAM used (out of 16GB)

**To reduce:**
- Decrease context window (fewer exchanges in memory)
- Use smaller Whisper model (tiny/base vs small)
- Reduce Ollama context size
- More aggressive garbage collection

### 5.4 Power Efficiency (24/7 Operation)

**Current optimizations:**
- Models loaded once at startup (not reloaded)
- Minimal SSD writes (tmpfs for audio)
- Efficient wake word detection (~1-2% CPU idle)

**Further improvements:**
- Lower wake word detection sample rate (if acceptable)
- Deeper sleep mode when idle (reduce CPU)
- Schedule breaks (auto-sleep at night)

---

## 6. Common Adjustments by Use Case

### 6.1 Beginner English Learner

**Recommended settings:**
```python
# More patient with pauses
silence_duration=5.0

# Longer idle timeout (needs thinking time)
idle_timeout=60.0

# More grammar correction in system prompt
system_prompt += "Gently correct grammar mistakes and explain why."

# Slower, simpler responses
system_prompt += "Use simple vocabulary and speak clearly. Short sentences."
```

### 6.2 Advanced/Fluent Speaker

**Recommended settings:**
```python
# Faster conversation flow
silence_duration=2.0
idle_timeout=20.0

# Natural conversation in system prompt
system_prompt += "Speak naturally. Rarely correct unless critical mistakes."

# Challenging vocabulary
system_prompt += "Use varied, advanced vocabulary. Discuss complex topics."
```

### 6.3 Business English Practice

**Recommended settings:**
```python
# Professional system prompt
system_prompt = """You are a business English conversation partner.
Discuss professional topics: meetings, presentations, negotiations, emails.
Use formal language and business vocabulary."""

# Fixed greeting
greeting = "Good morning! Ready for some business English practice?"

# Longer, detailed responses
system_prompt += "Provide detailed, professional responses with examples."
```

### 6.4 Noisy Environment

**Recommended settings:**
```python
# Higher VAD threshold (ignore background noise)
silence_threshold=0.03

# Higher wake word threshold (fewer false positives)
wake_threshold=0.7

# Longer cooldown (prevent noise triggers)
# Edit src/audio/wake_word.py line 137
self.cooldown_seconds = 3.0
```

### 6.5 Quick Daily Practice (Limited Time)

**Recommended settings:**
```python
# Fast conversation flow
silence_duration=1.5
idle_timeout=15.0

# Brief responses
system_prompt += "Keep all responses very brief - 1-2 sentences max."

# Quick greeting
greeting = "Hey! Let's practice!"
```

---

## 7. Configuration File Template

**Create a custom config:** `my_config.env`

```bash
# My Personal English Companion Settings

# Timing
VAD_SILENCE_DURATION=3.0
IDLE_TIMEOUT=30.0
WAKE_THRESHOLD=0.5

# Audio
AUDIO_DEVICE_INDEX=0
SILENCE_THRESHOLD=0.01

# Models
WHISPER_MODEL=small
OLLAMA_MODEL=llama3.2:3b

# Personality
GREETING_STYLE=casual  # casual, professional, encouraging
CORRECTION_LEVEL=medium  # low, medium, high
RESPONSE_LENGTH=short  # short, medium, long

# Learning Goals
FOCUS_AREAS=grammar,pronunciation,vocabulary
DIFFICULTY_LEVEL=intermediate
```

**Note:** Full config file support is a future enhancement. Currently, edit `voice_assistant.py` directly.

---

## 8. Testing Your Changes

### 8.1 Quick Test

```bash
# After making changes
python voice_assistant.py

# Say wake word and test one conversation
# Check if changes work as expected
```

### 8.2 Test Specific Features

```bash
# Test VAD settings
python test_vad_recording.py

# Test wake word sensitivity
python test_wake_word.py basic 30

# Test audio devices
python test_audio.py
```

### 8.3 Long-Term Testing

**Run for multiple sessions to verify:**
- Idle timeout works correctly
- Memory usage stays stable
- No performance degradation
- Settings feel natural over time

---

## 9. Troubleshooting Common Issues

### Issue: Sessions timeout too quickly

**Solution:** Increase `idle_timeout` from 30s to 60s

### Issue: Recording cuts off my speech

**Solution:** Increase `silence_duration` from 3.0s to 4.0s or 5.0s

### Issue: Too many false wake word detections

**Solution:** Increase `wake_threshold` from 0.5 to 0.6 or 0.7

### Issue: LLM responses are too long

**Solution:** Add to system prompt: "Keep responses to 2-3 sentences maximum."

### Issue: Not enough grammar correction

**Solution:** Update system prompt to emphasize correction and explanation

### Issue: Background noise triggers recording

**Solution:** Increase `silence_threshold` from 0.01 to 0.02 or 0.03

---

## 10. Requesting New Features

If you'd like to add features not listed here, create an issue or request:

**High Priority (Core functionality):**
- Grammar correction system with end-of-session summary
- Custom wake word training
- Better error recovery

**Medium Priority (Nice to have):**
- Progress tracking and analytics
- Topic suggestions and themed sessions
- Session persistence (resume conversations)

**Low Priority (Future enhancements):**
- Multiple user profiles
- Voice cloning for TTS
- Mobile app integration

---

## Quick Reference: Most Common Adjustments

| What to Change | File | Line | Current | Typical Range |
|----------------|------|------|---------|---------------|
| VAD silence duration | `voice_assistant.py` | 125 | 3.0s | 2.0-5.0s |
| Idle timeout | `voice_assistant.py` | 278 | 30.0s | 15-60s |
| Wake threshold | `voice_assistant.py` | 316 | 0.5 | 0.3-0.7 |
| Silence threshold | `voice_assistant.py` | 124 | 0.01 | 0.005-0.03 |
| Wake cooldown | `src/audio/wake_word.py` | 137 | 2.0s | 1.0-4.0s |
| Greeting prompt | `voice_assistant.py` | 238 | Dynamic | Custom text |

---

**Last Updated:** December 2024
**Project Phase:** Phase 2B Complete
**Status:** Production-ready for daily use

For questions or feature requests, see `CLAUDE.md` or project documentation.
