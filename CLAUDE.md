# CLAUDE.md

Quick reference for Claude Code working with English Companion NX project.

## Project Overview

**English Companion NX** - AI-powered conversational English practice system for NVIDIA Jetson Orin NX (16GB) running 24/7 as an always-available language learning companion.

**Current Status:** Phase 2B Complete - Always-on voice assistant with wake word detection, conversation sessions, VAD recording, and idle timeout. Working and tested!

## Critical Constraints

### Memory & SSD (MANDATORY)
- **11GB usable RAM** (16GB total - 5GB OS reserves)
- **~200MB typical daily SSD writes** - Well under 50GB limit
- **Single model load at startup** - Keep models in RAM
- **5-minute log flush intervals** - Buffer conversation logs
- **tmpfs for audio temp files** - Zero SSD writes for recordings

### Core Principle
**Load once, run forever** - Models loaded at service start, never reloaded unless service restarts.

## Infrastructure

### ✅ Required (Minimal)
- Ollama (LLM runtime, system service)
- tmpfs (/tmp) for temporary audio files
- JSONL file for conversation logging (buffered)
- systemd for service management

### ❌ NOT Required
- PostgreSQL (too heavy for conversation logs)
- Redis (no caching needed)
- Qdrant (no vector search needed initially)
- Docker/Podman (native Python service is simpler)

**Philosophy:** Start minimal, add complexity only when needed.

## Technology Stack (Phase 2B)

- **Runtime**: Python venv (--system-site-packages)
- **Audio**: Anker PowerConf S3 (16000 Hz)
- **Wake Word**: OpenWakeWord ("hey jarvis" / "alexa")
- **VAD**: Energy-based silence detection (3.0s timeout)
- **STT**: Whisper small (GPU, ~1-2s) + hallucination filter
- **LLM**: Ollama llama3.2:3b (~6-8s response)
- **TTS**: Coqui VITS (GPU, ~2.5s)
- **Sessions**: Conversation sessions with 30s idle timeout

## File Structure

```
english-companion-nx/
├── src/
│   ├── core/         # Config, memory monitoring
│   ├── audio/        # Wake word, VAD recorder, player
│   ├── speech/       # Whisper transcription, TTS synthesis
│   └── conversation/ # Context manager, LLM client, logger
├── voice_assistant.py        # Main entry point (Phase 2B)
├── conversation_prototype.py # Testing mode (Press Enter)
├── test_*.py                 # Component tests
├── debug_*.py                # Debug tools
├── .env                      # Configuration (gitignored)
├── requirements-jetson.txt   # Dependencies
├── VOICE_ASSISTANT_GUIDE.md  # User guide
├── FINE_TUNING_GUIDE.md      # Configuration tuning
└── MD/                       # Detailed documentation
    ├── ARCHITECTURE.md       # Data flow, performance
    ├── OPERATIONS.md         # Commands, monitoring
    ├── TROUBLESHOOTING.md    # Common issues, solutions
    ├── CODE_PATTERNS.md      # Development guidelines
    └── ...
```

## Quick Start

```bash
# On Jetson
cd ~/apps/english-companion-nx
source .venv/bin/activate
python voice_assistant.py
```

**Usage:**
- Say "hey jarvis" to start conversation session
- Ask multiple questions naturally
- 3s pause stops recording
- 30s idle timeout auto-ends session
- Ctrl+C to exit

## Key Files

- **`voice_assistant.py`** - Main entry (voice_assistant.py:40-350)
- **`src/audio/wake_word.py`** - OpenWakeWord dual detector
- **`src/audio/recorder.py`** - VAD recording (recorder.py:149-330)
- **`src/speech/transcription.py`** - Whisper + hallucination filter
- **`src/conversation/manager.py`** - Context management (last 20 exchanges)
- **`src/conversation/llm_client.py`** - Ollama API wrapper

## Essential Commands

```bash
# Service (when installed)
systemctl --user {start|stop|restart|status} english-companion-nx
journalctl --user -u english-companion-nx -f

# Testing
python test_audio.py              # Audio hardware
python test_wake_word.py basic 30 # Wake word (30s)
python test_vad_recording.py      # VAD recording
python debug_wake_word.py 30 hey_jarvis 0  # Debug scores

# Monitoring
free -h                           # Memory
cat /sys/class/thermal/thermal_zone*/temp  # Temperature
```

## Critical Reminders

1. **Load models ONCE** at startup, keep in RAM forever
2. **Use tmpfs** (/tmp/companion-audio/) for all audio files
3. **Stop/start wake detector** before/after VAD recording (audio device conflict!)
4. **Reuse sample rate** from wake detector (avoid re-probing)
5. **Filter hallucinations** before resetting idle timer
6. **Buffer writes** (5-min intervals for logs)
7. **Monitor memory** (cleanup every 10 conversations)
8. **Prune context** (last 20 exchanges max)

## Phase 2B Key Lessons

- Audio device must be freed before VAD recording (stop wake detector!)
- Whisper hallucinations must be filtered to prevent false activity
- ALSA warnings during startup are harmless (sample rate auto-detection)
- Stop trigger ("alexa") is optional - idle timeout handles session end
- Greeting must have separate error handling (always display, even if TTS fails)

## Documentation

**User Guides:**
- `VOICE_ASSISTANT_GUIDE.md` - End-user guide
- `FINE_TUNING_GUIDE.md` - Configuration tuning

**Technical Details:**
- `MD/ARCHITECTURE.md` - Data flow, resource allocation, performance
- `MD/OPERATIONS.md` - Service management, monitoring, maintenance
- `MD/TROUBLESHOOTING.md` - Common issues, emergency procedures
- `MD/CODE_PATTERNS.md` - Development guidelines, code examples
- `MD/CONVERSATION_SESSION_MODE.md` - Session mode design
- `MD/VAD_IMPLEMENTATION.md` - VAD technical details
- `MD/JETSON_MODELS.md` - Model testing results
- `MD/JETSON_SETUP.md` - Jetson-specific setup

**Deployment:**
- `MD/git-deployment-workflow.md` - Git-based deployment

## Current Phase

**✅ Phase 2B Complete:**
- OpenWakeWord dual detection (START/STOP)
- VAD-based recording with auto-stop
- Conversation sessions with idle timeout
- LLM-generated greetings
- Whisper hallucination filtering
- Memory monitoring and cleanup

**🚧 Phase 2C Planned:**
- systemd service setup
- Conversation logging (buffered JSONL)
- Log rotation
- Health monitoring scripts

**📋 Phase 3+ Planned:**
- MCP topic integration
- Grammar correction with session feedback
- Progress tracking and analytics

---

**Remember:** This is a 24/7 conversational companion. Reliability > Performance. Design for longevity, not peak performance.

**User Feedback:** "works really good so far. A bit finetuning and I have a really good conversation trainer."

**Last Updated:** December 2024
**Project Phase:** Phase 2B Complete
**Target Hardware:** Jetson Orin NX 16GB + Anker PowerConf S3
- mark progress on EPIC_...md files. Do not inflate them.