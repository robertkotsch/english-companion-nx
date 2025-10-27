# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with the English Companion NX project.

## Project Overview

**English Companion NX** - AI-powered conversational English practice system for NVIDIA Jetson Orin NX (16GB) running 24/7 as an always-available language learning companion.

## Critical Constraints

### Memory & SSD (MANDATORY)
- **11GB usable RAM** (16GB total - 5GB OS reserves)
- **~200MB typical daily SSD writes** - Well under 50GB limit
- **Single model load at startup** - Keep models in RAM
- **5-minute log flush intervals** - Buffer conversation logs
- **tmpfs for audio temp files** - Zero SSD writes for recordings

### Core Principle
**Load once, run forever** - Models loaded at service start, never reloaded unless service restarts.

## Infrastructure Requirements

### ✅ Required (Minimal)
```
Ollama             # LLM runtime (system service)
tmpfs (/tmp)       # Temporary audio files (RAM)
JSONL file         # Conversation logging (buffered)
systemd            # Service management
```

### ❌ NOT Required (Unlike Domain Radar)
```
PostgreSQL         # Too heavy for simple conversation logs
Redis              # No caching needed for conversational flow  
Qdrant             # No vector search needed initially
Docker/Podman      # Native Python service is simpler
```

### 🔧 Optional (Phase 4+)
```
SQLite             # If you want structured queries over conversations
Prometheus         # If you want metrics/monitoring
Grafana            # If you want visualization dashboards
Qdrant             # If you add semantic conversation search
```

**Philosophy:** Start minimal, add complexity only when needed. Domain Radar needs heavy infrastructure for data processing pipelines. English Companion NX is a conversational service - keep it simple!

## Architecture Quick Reference

### Technology Stack
- **Runtime**: Native Python (systemd user service)
- **Audio Hardware**: Anker PowerConf S3 (USB)
- **Speech-to-Text**: Whisper Medium (local, GPU-accelerated)
- **LLM**: Ollama with Llama 3.1 13B q4_0 (local, native)
- **TTS**: Coqui VITS (local, high quality)
- **Wake Word**: Porcupine (local, low-power)
- **Content**: MCP integration (existing topic curation system)

### System Architecture

```
┌─────────────────────────────────────────┐
│       Always-On Wake Word Detection      │
│         (Porcupine, <1% CPU)            │
└─────────────────────────────────────────┘
                ↓ (triggered)
┌─────────────────────────────────────────┐
│         Audio Recording (tmpfs)          │
│      (/tmp/companion-audio/*.wav)       │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│      Whisper Medium Transcription       │
│         (GPU, in-memory model)          │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│      Conversation Manager (Context)      │
│    + MCP Topic Integration (optional)   │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│    Llama 3.1 13B LLM (Ollama, cached)   │
│         + Grammar Analysis (bg)         │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│         Coqui VITS TTS Synthesis        │
│         (in-memory model)               │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│      Audio Output (Anker PowerConf)     │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│    Conversation Logger (buffered 5min)   │
│      /mnt/nvme/conversations.jsonl      │
└─────────────────────────────────────────┘
```

## Essential File Structure

```
english-companion-nx/
├── src/
│   ├── audio/
│   │   ├── wake_word.py          # Porcupine integration
│   │   ├── recorder.py           # Audio capture to tmpfs
│   │   └── player.py             # Audio playback
│   ├── speech/
│   │   ├── transcription.py      # Whisper wrapper
│   │   └── synthesis.py          # TTS wrapper
│   ├── conversation/
│   │   ├── manager.py            # Context management
│   │   ├── llm_client.py         # Ollama integration
│   │   ├── context.py            # Conversation history
│   │   └── logger.py             # Buffered conversation logging
│   ├── grammar/
│   │   └── correction.py         # Background grammar analysis
│   ├── mcp/
│   │   └── client.py             # Topic integration (optional)
│   ├── core/
│   │   ├── model_manager.py      # Singleton model loader
│   │   ├── memory_guard.py       # OOM prevention
│   │   └── config.py             # Configuration
│   └── main.py                   # Service entry point
├── config/
│   ├── system_prompt.txt         # LLM personality
│   └── settings.yaml             # Configuration
├── scripts/
│   ├── health_check.sh           # Daily monitoring
│   └── emergency_shutdown.py     # Safety procedures
├── logs/                         # Application logs (rotated)
├── .env                          # Environment config
├── requirements.txt              # Python dependencies
├── CLAUDE.md                     # This file
└── README.md                     # Project documentation
```

**Data storage location (NVMe):**
```
/mnt/nvme/companion/
├── conversations.jsonl           # Main conversation log (buffered writes)
├── conversations.db              # Optional SQLite (Phase 4+)
├── audio/                        # Optional saved recordings
└── backups/                      # Periodic backups
```

**No heavy infrastructure needed:**
- ❌ PostgreSQL (overkill for conversations)
- ❌ Redis (no caching needed)
- ❌ Qdrant (no vector search initially)

**Keep it simple:** JSONL file with buffered writes is sufficient for Phase 1-3.

## Critical System Files

**MUST READ before modifications:**

- `src/core/model_manager.py` - Singleton pattern, load-once strategy
- `src/core/memory_guard.py` - Memory monitoring, OOM prevention
- `src/conversation/manager.py` - Conversation buffering, context pruning
- `src/audio/recorder.py` - tmpfs usage for temp audio
- `main.py` - Service lifecycle, model loading

**Configuration:**
- `.env` - Environment variables (secure with chmod 600)
- `config/system_prompt.txt` - LLM personality definition
- `config/settings.yaml` - System parameters

## Data Flow (Critical Understanding)

### Conversation Flow

```
1. Wake Word Detected
   └─> Audio buffer activated
   
2. User Speech Recorded
   └─> Saved to /tmp/companion-audio/temp_<uuid>.wav
   └─> Transcribed with Whisper (from tmpfs)
   └─> File deleted immediately (no SSD write!)
   
3. Conversation Processing
   └─> Load conversation context (last N exchanges)
   └─> Optional: Fetch MCP topic if relevant
   └─> Send to Llama 3.1 13B (cached in RAM)
   └─> Background: Grammar analysis (if enabled)
   
4. Response Generation
   └─> LLM generates response
   └─> Optionally integrate grammar correction
   └─> Synthesize with Coqui TTS (from RAM)
   
5. Output & Logging
   └─> Play audio through speaker
   └─> Buffer conversation entry (write every 5 min)
   └─> Update context for next exchange
```

### Memory Format

**Conversation Log Entry:**
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

**Context Window Format:**
```python
[
  {"role": "user", "content": "How are you?"},
  {"role": "assistant", "content": "I'm doing well, thanks!"},
  {"role": "user", "content": "Tell me about..."}
]
```

## Network & Deployment

**Jetson Network:**
- IP: `192.168.x.x` (configure in your network)
- Service port: 8000 (if using API mode)
- Metrics port: 8001 (Prometheus)
- Path: `~/apps/english-companion-nx`

**Git-Based Deployment Workflow:**

```
Dev Machine → git push → GitHub → git pull → Jetson
```

**Principle:** Git is single source of truth. Jetson is read-only from GitHub.

### Initial Setup (One-Time)

**On Jetson:**
```bash
# Generate SSH deploy key
ssh-keygen -t ed25519 -C "jetson-english-companion-nx"
cat ~/.ssh/id_ed25519.pub
# Add to GitHub: Settings → Deploy Keys

# Clone repository
mkdir -p ~/apps
cd ~/apps
git clone git@github.com:<your-username>/english-companion-nx.git
cd english-companion-nx

# Setup environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
nano .env  # Customize
chmod 600 .env
```

### Daily Deployment

**On dev machine:**
```bash
# Develop locally
git add .
git commit -m "feat: Add new feature"
git push origin main
```

**On Jetson:**
```bash
# Quick update
cd ~/apps/english-companion-nx
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt
systemctl --user restart english-companion-nx

# Or use automation
make deploy-update
```

**See [Git Deployment Workflow](./git-deployment-workflow.md) for complete guide.**

## Essential Commands

### Service Management
```bash
# Start service
systemctl --user start english-companion-nx

# Stop service
systemctl --user stop english-companion-nx

# Restart service
systemctl --user restart english-companion-nx

# Check status
systemctl --user status english-companion-nx

# View logs (live)
journalctl --user -u english-companion-nx -f

# View logs (last 100 lines)
journalctl --user -u english-companion-nx -n 100
```

### Model Management
```bash
# Pull models (one-time setup)
ollama pull llama3.1:13b-instruct-q4_0
ollama pull nomic-embed-text  # For future embeddings

# Verify models loaded
ollama list

# Check Ollama status
systemctl status ollama
```

### Testing
```bash
# Test individual components
python -m src.speech.transcription  # Test Whisper
python -m src.speech.synthesis      # Test TTS
python -m src.conversation.llm_client  # Test LLM

# Test full conversation flow
python test_conversation_flow.py

# Memory pressure test
python scripts/memory_pressure_test.py
```

### Monitoring
```bash
# Check system resources
jtop  # Jetson stats (install: sudo pip3 install jetson-stats)

# Check memory usage
free -h

# Check temperature
cat /sys/class/thermal/thermal_zone*/temp

# Check SSD health
sudo smartctl -a /dev/nvme0n1

# View conversation stats
python scripts/conversation_stats.py
```

### Maintenance
```bash
# Rotate logs manually
sudo logrotate -f /etc/logrotate.d/english-companion-nx

# Check disk usage
du -sh ~/apps/english-companion-nx/*

# Clean old conversations (keeps last 30 days)
python scripts/cleanup_old_conversations.py --days 30

# Backup conversations
python scripts/backup_conversations.py
```

## Development Guidelines

### SSD Protection (ABSOLUTE RULES)

✅ **DO:**
- Buffer conversation logs (5-min flush intervals)
- Use `/tmp` (tmpfs) for all audio temp files
- Keep models in RAM (load once at startup)
- Batch database writes if using SQLite
- Compress old logs automatically

❌ **NEVER:**
- Save every audio recording to SSD
- Write logs on every conversation
- Reload models during operation
- Enable unnecessary file logging
- Use SSD for scratch/temp data

### Memory Safety

✅ **DO:**
- Load all models at service startup
- Prune conversation context (keep last 10-20 exchanges)
- Run garbage collection periodically (every 10 conversations)
- Clear CUDA cache after GPU operations
- Monitor memory with MemoryGuard

❌ **NEVER:**
- Keep unlimited conversation history in memory
- Load models on-demand (defeats caching)
- Ignore memory warnings
- Run without MemoryMax systemd limits
- Accumulate audio buffers

### Code Patterns

**Model Loading (Singleton):**
```python
# GOOD: Load once, reuse forever
class ModelManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.load_models()
        return cls._instance
    
    def load_models(self):
        self.whisper = whisper.load_model("medium")
        self.tts = load_tts_model()
        # Keep in RAM forever

model_manager = ModelManager()  # Load once at startup
```

**Audio Recording (tmpfs):**
```python
# GOOD: Record to RAM, delete immediately
TEMP_DIR = '/tmp/companion-audio'
temp_file = os.path.join(TEMP_DIR, f'temp_{uuid4()}.wav')
record_audio(temp_file)
transcript = whisper.transcribe(temp_file)
os.remove(temp_file)  # No SSD write!
```

**Conversation Logging (Buffered):**
```python
# GOOD: Buffer writes, flush periodically
class ConversationLogger:
    def __init__(self, flush_interval=300):
        self.buffer = []
        self.flush_interval = flush_interval
    
    def log(self, user_msg, assistant_msg):
        self.buffer.append({
            'timestamp': datetime.now().isoformat(),
            'user': user_msg,
            'assistant': assistant_msg
        })
        
        if time.time() - self.last_flush > self.flush_interval:
            self.flush()  # Single write operation
```

**Memory Cleanup (Periodic):**
```python
# GOOD: Clean up after every 10 conversations
def process_conversation(self):
    # ... conversation logic ...
    
    self.count += 1
    if self.count % 10 == 0:
        gc.collect()
        torch.cuda.empty_cache()
        memory_guard.check_status()
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

## Configuration

### Environment Variables

```bash
# .env file (chmod 600!)

# Ollama
OLLAMA_HOST=127.0.0.1:11434
OLLAMA_MODEL=llama3.1:13b-instruct-q4_0

# MCP (optional - Phase 3+)
MCP_SERVER_URL=http://localhost:8080

# Audio
AUDIO_TEMP_DIR=/tmp/companion-audio
AUDIO_SAMPLE_RATE=16000

# Logging
LOG_LEVEL=INFO
LOG_BUFFER_INTERVAL=300  # 5 minutes
LOG_DIR=/mnt/nvme/companion/logs

# Conversation Storage (Simple JSONL)
CONVERSATION_LOG=/mnt/nvme/companion/conversations.jsonl
CONVERSATION_BUFFER_INTERVAL=300  # 5 minutes
CONVERSATION_CONTEXT_SIZE=20  # Last N exchanges to keep in memory

# Optional: SQLite (Phase 4+)
# CONVERSATION_DB=/mnt/nvme/companion/conversations.db

# Memory
MEMORY_WARNING_THRESHOLD=0.85
MEMORY_CRITICAL_THRESHOLD=0.95

# Thermal
THERMAL_WARNING_TEMP=70
THERMAL_CRITICAL_TEMP=80
```

### Data Storage Strategy

**Phase 1-3 (Minimal):**
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

**Phase 4+ (Optional SQLite):**
```python
# If you need structured queries
# /mnt/nvme/companion/conversations.db

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

# Still use buffered batch inserts!
# Don't write on every conversation
```

### System Prompt

```text
# config/system_prompt.txt

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

## Emergency Procedures

### Memory Critical (>95%)

```bash
# Immediate action
systemctl --user restart english-companion-nx

# If persistent
sudo swapoff -a && sudo swapon -a  # Clear swap
sudo sync && sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'  # Clear cache

# Check for memory leaks
python scripts/memory_leak_detector.py
```

### Thermal Critical (>80°C)

```bash
# Reduce power mode
sudo nvpmodel -m 2  # Set to 10W mode

# Stop service temporarily
systemctl --user stop english-companion-nx

# Check fan
# Ensure active cooling is working

# Wait for cooldown (<70°C)
watch -n 1 'cat /sys/class/thermal/thermal_zone*/temp'

# Resume
sudo nvpmodel -m 0  # Back to 25W
systemctl --user start english-companion-nx
```

### Service Won't Start

```bash
# Check logs
journalctl --user -u english-companion-nx -n 50

# Common issues:
# 1. Model not loaded
ollama list  # Verify models present

# 2. Insufficient memory
free -h  # Check available RAM

# 3. Port conflict
sudo ss -ltnp | grep 8000

# 4. Permission issues
ls -la .env  # Should be 600
ls -la /tmp/companion-audio  # Should be writable

# Manual start (debug)
cd ~/apps/english-companion-nx
source .venv/bin/activate
python main.py  # See errors directly
```

### SSD Health Degradation

```bash
# Check SMART data
sudo smartctl -a /dev/nvme0n1 | grep -E "Percentage Used|Data Units Written"

# If >70% wear:
# 1. Backup conversations
python scripts/backup_conversations.py --destination /backup/

# 2. Plan SSD replacement
# 3. Continue monitoring weekly

# If >90% wear:
# URGENT: Replace SSD immediately
```

## Monitoring & Health Checks

### Daily Health Check Script

```bash
#!/bin/bash
# scripts/daily_health_check.sh

echo "=== English Companion NX Health Check ==="
echo "Date: $(date)"

echo -e "\n--- Memory Status ---"
free -h | grep Mem

echo -e "\n--- Temperature ---"
temp=$(cat /sys/class/thermal/thermal_zone0/temp)
echo "CPU: $((temp / 1000))°C"

echo -e "\n--- SSD Health ---"
sudo smartctl -a /dev/nvme0n1 | grep "Percentage Used"

echo -e "\n--- Service Status ---"
systemctl --user is-active english-companion-nx

echo -e "\n--- Recent Conversations ---"
journalctl --user -u english-companion-nx --since today | grep -c "Conversation"

echo -e "\n--- Disk Usage ---"
du -sh ~/apps/english-companion-nx/logs
du -sh /mnt/nvme/companion/
```

**Schedule in crontab:**
```bash
0 2 * * * ~/apps/english-companion-nx/scripts/daily_health_check.sh >> ~/health_checks.log
```

### Prometheus Metrics

```python
# Exposed on http://localhost:8001/metrics

# Counters
companion_conversations_total
companion_model_loads_total

# Gauges  
companion_memory_bytes
companion_temperature_celsius
companion_response_time_seconds

# Histograms
companion_transcription_duration_seconds
companion_llm_generation_duration_seconds
companion_tts_synthesis_duration_seconds
```

## Testing Strategy

### Unit Tests
```bash
# Test individual components
pytest tests/test_audio.py
pytest tests/test_speech.py
pytest tests/test_conversation.py
pytest tests/test_grammar.py
```

### Integration Tests
```bash
# Test full flow
pytest tests/test_conversation_flow.py

# Test model loading
pytest tests/test_model_manager.py

# Test memory safety
pytest tests/test_memory_guard.py
```

### Manual Testing
```bash
# Test wake word
python -m src.audio.wake_word

# Test full conversation
python test_interactive.py

# Test with topic integration
python test_with_mcp.py
```

## Performance Targets

### Latency Goals
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

### Accuracy Goals
```
Wake word accuracy:       >95%
Transcription (WER):      <5%
Grammar detection:        >80% precision
User satisfaction:        >85% (subjective)
```

### Reliability Goals
```
Uptime:                   >99.5% (24/7)
Memory stability:         No leaks over 7 days
Service restarts:         <1 per month
Mean time to recovery:    <5 minutes
```

## Common Pitfalls & Solutions

### Pitfall 1: Model Reloading
**Problem:** Service slow after a few hours
**Cause:** Models being reloaded from disk
**Solution:** Use singleton ModelManager, verify models stay in RAM

### Pitfall 2: Memory Leaks
**Problem:** Memory usage grows over time
**Cause:** Conversation context not pruned, CUDA cache not cleared
**Solution:** Implement periodic cleanup (see code patterns)

### Pitfall 3: SSD Wear
**Problem:** High SSD writes
**Cause:** Logging every conversation immediately
**Solution:** Buffer writes (5-min intervals)

### Pitfall 4: Thermal Throttling
**Problem:** Slow responses after 1-2 hours
**Cause:** Overheating, thermal throttling
**Solution:** Ensure active cooling, monitor temps, use adaptive power modes

### Pitfall 5: Context Overflow
**Problem:** LLM responses become incoherent
**Cause:** Too much context, token limit exceeded
**Solution:** Prune to last 10-20 exchanges, summarize older context

## Best Practices Checklist

### Startup
- [ ] Models loaded once (Whisper, LLM, TTS)
- [ ] tmpfs directory created (/tmp/companion-audio)
- [ ] Conversation logger initialized with buffering
- [ ] Memory guard activated
- [ ] Thermal monitor started
- [ ] Prometheus metrics server started

### During Operation
- [ ] Audio recordings to tmpfs only
- [ ] Conversation logs buffered (5-min flush)
- [ ] Context pruned (last 20 exchanges max)
- [ ] Garbage collection every 10 conversations
- [ ] Memory checked before heavy operations
- [ ] Temperature monitored every 30s

### Maintenance
- [ ] Daily health check runs (cron)
- [ ] Logs rotated (weekly)
- [ ] Old conversations archived (monthly)
- [ ] SSD health checked (weekly)
- [ ] Backups created (weekly)
- [ ] System updates applied (monthly)

## Documentation Reference

**Project Documentation:**
- `README.md` - Project overview, setup instructions
- `ai-english-companion-nx-project-spec.md` - Complete specification
- `jetson-orin-nx-deployment-guide.md` - General Jetson deployment
- `CLAUDE.md` - This file (development guide)

**External Resources:**
- Whisper: https://github.com/openai/whisper
- Ollama: https://ollama.ai/
- Coqui TTS: https://github.com/coqui-ai/TTS
- Porcupine: https://picovoice.ai/platform/porcupine/
- Jetson Docs: https://docs.nvidia.com/jetson/

## Current Status

### ✅ Completed
- [x] Architecture designed
- [x] Hardware selected (Anker PowerConf S3)
- [x] Resource management patterns defined
- [x] SSD protection strategies documented
- [x] Memory safety guidelines established

### 🚧 In Progress
- [ ] Phase 1: Core audio pipeline
- [ ] Phase 2: Wake word + conversation
- [ ] Phase 3: MCP integration
- [ ] Phase 4: Grammar correction
- [ ] Phase 5: Polish & optimization

### 📋 Planned
- [ ] Advanced features (voice cloning, emotion detection)
- [ ] Mobile companion app
- [ ] Multi-language support
- [ ] Conversation analytics dashboard

---

## 🎯 CRITICAL REMINDERS

1. **Load models ONCE** at service startup, keep in RAM
2. **Use tmpfs** for all temporary audio files
3. **Buffer writes** (5-min intervals for logs)
4. **Monitor memory** actively (OOM will crash service)
5. **Check temperature** regularly (thermal throttling kills performance)
6. **Prune context** (keep last 20 exchanges max)
7. **Set resource limits** (systemd MemoryMax)
8. **Test under load** (run for 24+ hours before production)

---

**Remember:** This is a 24/7 conversational companion. Reliability > Performance. The device should "just work" every day for years. Design for longevity, not peak performance.

**Last Updated:** October 27, 2025
**Project Phase:** Planning & Design
**Target Hardware:** Jetson Orin NX 16GB + Anker PowerConf S3
