# Conversation Session Mode with Stop Trigger

## Overview

The voice assistant now supports **conversation sessions** - extended conversations with multiple Q&A exchanges that continue until you say a stop trigger word.

## How It Works

### Traditional Mode (Old)
```
Say "hey jarvis" → Ask one question → Get answer → Say "hey jarvis" again...
```

### Conversation Session Mode (New)
```
Say "hey jarvis" → SESSION STARTS
  ├─ Ask question 1 → Get answer 1
  ├─ Ask question 2 → Get answer 2
  ├─ Ask question 3 → Get answer 3
  └─ Say "alexa" → SESSION ENDS
Back to listening for "hey jarvis"...
```

## Usage

### Start a Session

**Say:** `"hey jarvis"`

```
🎯 WAKE WORD DETECTED! (Session #1)
============================================================
💬 CONVERSATION SESSION ACTIVE
============================================================
Options:
  - Say 'alexa' to end this session
  - Or just start speaking for Q&A
============================================================

👂 Listening (speak for Q&A, or say 'alexa' to exit)...
```

### During a Session

Just **start speaking** after you hear the system say it's listening. No need to say "hey jarvis" again!

**Example conversation:**
```
You: "What's the weather like today?"
Assistant: [gives weather info]

You: "How about tomorrow?"
Assistant: [gives tomorrow's weather]

You: "Thanks, that's helpful"
Assistant: [responds]
```

### End a Session

**Say:** `"alexa"` (or your configured stop word)

```
🛑 STOP WORD DETECTED - Ending conversation session
Session summary: 3 conversations

🎧 Returning to wake word listening...
```

## Configuration

### Default Settings

- **Wake word:** `hey_jarvis` (starts session)
- **Stop word:** `alexa` (ends session)
- **Thresholds:** 0.5 for both

### Command Line Options

```bash
# Use defaults
python voice_assistant.py

# Custom wake and stop words
python voice_assistant.py hey_jarvis timer 0.5 0.6 0

# Full syntax
python voice_assistant.py [WAKE_MODEL] [STOP_MODEL] [WAKE_THRESH] [STOP_THRESH] [DEVICE]
```

**Available models:**
- `hey_jarvis`
- `alexa`
- `hey_mycroft`
- `timer`

### Examples

**Use "timer" as stop word:**
```bash
python voice_assistant.py hey_jarvis timer 0.5 0.5 0
```

**Adjust thresholds:**
```bash
python voice_assistant.py hey_jarvis alexa 0.6 0.7 0
```

## Benefits

### ✅ Natural Conversations

- Multiple questions without repeating wake word
- Maintains context across exchanges
- More like talking to a real person

### ✅ Efficient

- No need to say "hey jarvis" for every question
- Faster follow-up questions
- Saves 2+ seconds per exchange

### ✅ Flexible

- Can have quick 1-question sessions
- Or extended 10+ question conversations
- You control the session length

## How It Detects Stop vs Speech

The system uses a **2-second timeout** to differentiate:

1. **Listen for 2 seconds**
   - If stop word detected → End session
   - If nothing detected → Assume you want to speak → Record with VAD

2. **Recording with VAD**
   - Beep signals recording start
   - Speak naturally
   - Stops after 3 seconds of silence
   - Transcribes and responds

3. **Back to listening**
   - After response, listens again
   - Either for stop word or next question

## Example Session

```
🎧 Listening for wake word...

[You say: "hey jarvis"]

🎯 WAKE WORD DETECTED! (Session #1)
============================================================
💬 CONVERSATION SESSION ACTIVE
============================================================

👂 Listening (speak for Q&A, or say 'alexa' to exit)...

[You start speaking: "What is the capital of France?"]

🎤 Recording with Voice Activity Detection...
🔴 [BEEP] Start speaking now...
🗣️  Speech detected...
✅ Recording complete (4.3s) - Detected 3.0s of silence

🧠 Transcribing...
👤 You: What is the capital of France?
💭 Thinking...
✅ Response generated (6.8s)
🔊 Synthesizing speech...
🤖 Assistant: The capital of France is Paris...

📊 Context: 1 exchanges in memory
💾 Memory: 45.2% used (7.2GB / 16.0GB)
⏱️  Total: 14.3s

👂 Listening (speak for Q&A, or say 'alexa' to exit)...

[You continue: "What is Paris famous for?"]

🎤 Recording with Voice Activity Detection...
[... same flow ...]

👂 Listening (speak for Q&A, or say 'alexa' to exit)...

[You say: "alexa"]

🛑 STOP WORD DETECTED - Ending conversation session
Session summary: 2 conversations

🎧 Returning to wake word listening...

[Ready for next session...]
```

## Tips

### For Best Results

1. **Wait for the prompt** before speaking or saying stop word
   - Look for: "👂 Listening (speak for Q&A, or say 'alexa' to exit)..."

2. **Clear pronunciation** for stop word
   - Say "alexa" clearly and at normal volume
   - Same rules as wake word detection

3. **Don't mix stop word with questions**
   - Either say stop word alone
   - Or start asking a question
   - Don't say both at once

### Common Patterns

**Quick single question:**
```
"hey jarvis" → [question] → "alexa"
(1 exchange session)
```

**Extended conversation:**
```
"hey jarvis" → [Q1] → [Q2] → [Q3] → [Q4] → "alexa"
(4 exchange session)
```

**Context building:**
```
"hey jarvis"
→ "Tell me about Paris"
→ "What about its history?"
→ "How about the Eiffel Tower?"
→ "alexa"

(All questions maintain context!)
```

## Troubleshooting

### Stop word not detected

**Symptoms:**
- Say "alexa" but session continues
- System starts recording instead

**Solutions:**
1. Speak more clearly: "uh-LEX-uh"
2. Increase volume slightly
3. Lower threshold: `python voice_assistant.py hey_jarvis alexa 0.5 0.3 0`
4. Try different stop word: `python voice_assistant.py hey_jarvis timer`

### Accidentally triggers stop during speech

**Symptoms:**
- Session ends when you didn't mean to
- Mentioned "alexa" in your question

**Solutions:**
1. Use different stop word: `timer` or `hey_mycroft`
2. Raise threshold: `python voice_assistant.py hey_jarvis alexa 0.5 0.7 0`
3. Avoid mentioning stop word in questions

### Session starts recording automatically

**Expected behavior!** If you don't say stop word within 2 seconds, system assumes you want to speak and starts recording. This is by design for smooth conversations.

## Future Enhancements

Planned improvements for future versions:

1. **Custom stop words**
   - Train custom "goodbye" or "stop listening" models
   - More natural exit phrases

2. **Automatic session timeout**
   - End session after N minutes of inactivity
   - Prevents forgotten sessions

3. **Session context preservation**
   - Save session context for later continuation
   - "Resume previous conversation"

4. **Multi-user sessions**
   - Different wake/stop words per user
   - User identification and personalization

## Statistics

The system tracks session and conversation statistics:

```
📊 Final Statistics
============================================================
Total sessions: 5
Total conversations: 23
Wake word detections: 5
Stop word detections: 5
============================================================
```

**Metrics:**
- **Sessions:** How many times you said wake word
- **Conversations:** Total Q&A exchanges across all sessions
- **Average:** conversations ÷ sessions = avg questions per session

## See Also

- `VOICE_ASSISTANT_GUIDE.md` - General voice assistant usage
- `VAD_IMPLEMENTATION.md` - Voice Activity Detection details
- `WAKE_WORD_ALTERNATIVES.md` - Wake word model selection

---

**Status:** Phase 2B Complete with Conversation Sessions
**Last Updated:** December 2024
**Tested On:** Jetson Orin NX 16GB with Anker PowerConf S3
