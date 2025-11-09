# Personality Profiles

This directory contains personality profile files that define how the English Companion behaves during conversations.

## Available Personalities

### 🎯 casual_friend (Default)
Friendly, relaxed conversation partner focused on natural, engaging dialogue. Light grammar correction (max 1 per conversation). Best for building confidence and enjoying conversations.

**Use when:** You want to practice speaking naturally without feeling judged.

### 👨‍🏫 patient_teacher
Warm, encouraging teacher who provides structured conversations with helpful feedback. More grammar correction (2-3 per conversation) with brief explanations.

**Use when:** You want to improve while still having natural conversations.

### 🗣️ native_speaker
Native English speaker using authentic, everyday language including idioms and colloquial expressions. Minimal grammar correction, maximum exposure to natural speech.

**Use when:** You want to learn how native speakers actually talk.

### 📚 grammar_coach
Focused grammar coach who actively corrects errors (3-4 per conversation) with detailed explanations and examples. Prioritizes proper language structure.

**Use when:** You're preparing for exams or want to master grammar rules.

## How to Switch Personalities

### 1. Edit your `.env` file
```bash
# In your .env file, change this line:
PERSONALITY_PROFILE=casual_friend

# To one of these options:
PERSONALITY_PROFILE=patient_teacher
PERSONALITY_PROFILE=native_speaker
PERSONALITY_PROFILE=grammar_coach
```

### 2. Restart the voice assistant
```bash
# If running as systemd service:
systemctl --user restart english-companion-nx

# If running manually:
# Press Ctrl+C to stop, then run again:
python voice_assistant.py
```

The new personality will be loaded on startup!

## Creating Custom Personalities

You can create your own personality by adding a new `.txt` file to this directory:

1. **Create a new file:** `personalities/my_custom_personality.txt`
2. **Write the personality prompt** (see existing files for examples)
3. **Update `.env`:** `PERSONALITY_PROFILE=my_custom_personality`
4. **Restart** the voice assistant

### Tips for Writing Personalities

- Be specific about tone and behavior
- Define response length preferences (1-2 sentences, 3-4 sentences, etc.)
- Specify grammar correction frequency (none, light, moderate, heavy)
- Include examples of the type of language to use
- Keep it concise but clear

## Examples

```bash
# Start with patient_teacher for structured learning
PERSONALITY_PROFILE=patient_teacher

# Switch to native_speaker once comfortable
PERSONALITY_PROFILE=native_speaker

# Use grammar_coach before important presentations
PERSONALITY_PROFILE=grammar_coach

# Return to casual_friend for relaxed practice
PERSONALITY_PROFILE=casual_friend
```

## Technical Details

- Personality files are loaded once at startup (part of the "load once, run forever" principle)
- Stored as plain text for easy editing
- Located at: `personalities/{PERSONALITY_PROFILE}.txt`
- Fallback to default personality if file not found
- Changes require service restart to take effect
