# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**English Companion NX** - AI-powered conversational English practice system for NVIDIA Jetson Orin NX (16GB) running 24/7 as an always-available language learning companion.

**Current Status:** Phase 2B Complete + Zoo Architecture Implementation

**Core Principle:** Load once, run forever. Models loaded at service start, never reloaded unless service restarts.

## Critical Constraints (MANDATORY)

### Hardware Limits
- **11GB usable RAM** (16GB total - 5GB OS reserves)
- **~200MB daily SSD writes** (well under 50GB safety limit)
- **Single model load at startup** - keep models in RAM
- **tmpfs for audio temp files** - zero SSD writes for recordings

### Architecture Philosophy
- Start minimal, add complexity only when needed
- Reliability > Performance
- Design for longevity, not peak performance
- Git as source of truth (dev → GitHub → Jetson pull-only)

### Infrastructure: ✅ Required vs ❌ NOT Required
**✅ Required:**
- Ollama (LLM runtime, system service)
- tmpfs (/tmp) for temporary audio files
- JSONL file for conversation logging (buffered)
- systemd for service management

**❌ NOT Required (initially):**
- PostgreSQL (too heavy for conversation logs)
- Redis (no caching needed)
- Qdrant (no vector search needed initially)
- Docker/Podman (native Python service is simpler)

## Technology Stack

- **Runtime:** Python venv (--system-site-packages)
- **Audio:** Anker PowerConf S3 (16000 Hz)
- **Wake Word:** OpenWakeWord ("hey jarvis" / "alexa")
- **VAD:** Energy-based silence detection (3.0s timeout)
- **STT:** Whisper small (GPU, ~1-2s) + hallucination filter
- **LLM:** Ollama qwen2.5:3b-instruct (faster, better grammar/determinism)
- **TTS:** Coqui VITS (GPU, ~2.5s)
- **Sessions:** Conversation sessions with 30s idle timeout

## Essential Commands

```bash
# Development
cd ~/apps/english-companion-nx
source .venv/bin/activate
python voice_assistant.py              # Main voice assistant (Phase 2B)
python conversation_prototype.py       # Testing mode (Press Enter)

# Testing
python test_audio.py                   # Audio hardware
python test_wake_word.py basic 30      # Wake word (30s)
python test_vad_recording.py           # VAD recording
python debug_wake_word.py 30 hey_jarvis 0  # Debug wake word scores
python -m pytest                       # Run all tests (when on dev machine)

# Service Management (when installed)
systemctl --user {start|stop|restart|status} english-companion-nx
journalctl --user -u english-companion-nx -f

# Deployment (Jetson only)
make deploy-update     # Pull from GitHub + restart service
make deploy-status     # Service status
make deploy-logs       # View recent logs
make deploy-check      # Pre-deployment health check

# Monitoring
free -h                                # Memory usage
cat /sys/class/thermal/thermal_zone*/temp  # Temperature
```

## Project Structure

```
english-companion-nx/
├── src/
│   ├── core/         # Config, memory monitoring
│   ├── audio/        # Wake word, VAD recorder, player
│   ├── speech/       # Whisper transcription, TTS synthesis
│   ├── conversation/ # Context manager, LLM client, logger
│   └── zoo/          # NEW: Zoo agent system (listeners, coaching, memory)
│       ├── signals.py           # Signal dataclasses
│       ├── zoo_logger.py        # Zoo-specific logging
│       ├── listeners/           # Passive observer agents
│       │   ├── grammar_giraffe.py
│       │   ├── filler_falcon.py
│       │   └── ...
│       ├── coaching/            # Active coaching agents
│       ├── memory/              # Progress tracking
│       └── flow/                # Orchestration
├── voice_assistant.py           # Main entry point (Phase 2B)
├── conversation_prototype.py    # Testing mode
├── test_*.py                    # Component tests
├── debug_*.py                   # Debug tools
├── .env                         # Configuration (gitignored)
├── requirements-jetson.txt      # Dependencies
└── MD/                          # Detailed documentation
    ├── ARCHITECTURE.md
    ├── CODE_PATTERNS.md         # Development patterns (READ THIS!)
    ├── OPERATIONS.md
    └── Zoo/
        └── EPIC_*.md            # Implementation plans
```

## Key Development Patterns

### 1. Audio Device Management (CRITICAL!)
**Must stop wake detector before VAD recording** - audio device can only be accessed by one process at a time.

```python
# Wake word detection loop
result = self.wake_detector.detect_once(timeout=2.0)

if result == WakeWordType.NONE:  # User wants to speak
    self.wake_detector.stop()       # FREE audio device
    self.handle_conversation()      # VAD recording can now access device
    self.wake_detector.start()      # Resume wake word detection
```

### 2. Model Loading (Singleton Pattern)
Load models ONCE at startup, keep in RAM forever. Never reload during operation.

```python
class VoiceAssistant:
    def __init__(self):
        # Load at startup - keep in RAM until service restarts
        self.wake_detector = WakeWordDetector(...)
        self.transcription = TranscriptionService()  # Whisper small
        self.synthesis = SynthesisService()          # Coqui VITS
        self.conversation = ConversationManager()
```

### 3. SSD Protection (ABSOLUTE RULES)
- ✅ Use `/tmp` (tmpfs) for all audio temp files
- ✅ Buffer conversation logs (5-min flush intervals)
- ✅ Keep models in RAM (load once at startup)
- ❌ NEVER save every audio recording to SSD
- ❌ NEVER reload models during operation

### 4. Memory Safety
- Prune conversation context (keep last 20 exchanges)
- Run garbage collection periodically (every 10 conversations)
- Monitor memory with MemoryMonitor
- Clear CUDA cache after GPU operations

### 5. Sample Rate Reuse
Detect sample rate once at init, reuse everywhere to avoid re-probing ALSA.

```python
# Wake detector finds working sample rate
self.wake_detector = WakeWordDetector(audio_device_index=0)
self.detected_sample_rate = self.wake_detector.device_sample_rate

# Reuse in VAD recording (no re-probing!)
self.recorder = AudioRecorder(sample_rate=self.detected_sample_rate)
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

## Zoo Architecture (New Addition)

**Signal Flow Pattern:**
```
User Speech → Whisper STT
    ↓
[Listener Agents] → emit signals (grammar, fillers, tempo, vocab)
    ↓
[OrchestratorOctopus] → prioritize signals, decide action
    ↓
[TaskTiger/CoachCoyote] → deliver coaching feedback
    ↓
[Memory Agents] → update progress
```

**Key Principles:**
- Listeners are passive observers (analyze, emit signals)
- Orchestrator decides what to act on
- Coaching agents deliver feedback
- Memory agents track progress over time
- Use buffered logging to avoid SSD writes

## Documentation Map

**Quick Reference:**
- `CLAUDE.md` (this file) - Development quick reference
- `MD/CODE_PATTERNS.md` - Detailed coding patterns (READ BEFORE CODING!)
- `MD/ARCHITECTURE.md` - System architecture and data flow
- `MD/OPERATIONS.md` - Service management and monitoring

**User Guides:**
- `VOICE_ASSISTANT_GUIDE.md` - End-user guide
- `FINE_TUNING_GUIDE.md` - Configuration tuning

**Implementation Plans:**
- `MD/Zoo/EPIC_1_MVP_IMPLEMENTATION.md` - Zoo system implementation
- Mark progress on EPIC_*.md files (do not inflate them)

**Technical Details:**
- `MD/TROUBLESHOOTING.md` - Common issues and solutions
- `MD/JETSON_MODELS.md` - Model testing results
- `MD/JETSON_SETUP.md` - Jetson-specific setup
- `MD/git-deployment-workflow.md` - Git-based deployment

## Configuration

Copy `.env.example` to `.env` and customize. Key settings:

```bash
# LLM
OLLAMA_MODEL=qwen2.5:3b-instruct  # Recommended for Jetson Orin NX

# Audio
AUDIO_DEVICE_NAME=PowerConf       # Auto-finds matching device
AUDIO_TEMP_DIR=/tmp/companion-audio

# Models
WHISPER_MODEL=small               # Recommended for Jetson
USE_GPU=true

# Conversation
CONVERSATION_CONTEXT_SIZE=20      # Last N exchanges in memory
CONVERSATION_BUFFER_INTERVAL=300  # 5-min flush interval
```

## Development Workflow

**On Dev Machine:**
```bash
# Make changes, test if possible
git add .
git commit -m "feat: Add feature X"
git push origin main
```

**On Jetson:**
```bash
cd ~/apps/english-companion-nx
make deploy-update  # Pull + restart service
make deploy-logs    # Check if working
```

## Current Phase Status

**✅ Phase 2B Complete:**
- OpenWakeWord dual detection (START/STOP)
- VAD-based recording with auto-stop
- Conversation sessions with idle timeout
- LLM-generated greetings
- Whisper hallucination filtering
- Memory monitoring and cleanup

**🚧 Zoo System In Progress:**
- Signal-based listener architecture
- Grammar detection (GrammarGiraffe)
- Filler word tracking (FillerFalcon)
- Coaching feedback system

**📋 Planned:**
- systemd service setup
- Conversation logging (buffered JSONL)
- MCP topic integration
- Progress tracking and analytics

---

**Target Hardware:** Jetson Orin NX 16GB + Anker PowerConf S3
**Last Updated:** January 2025

