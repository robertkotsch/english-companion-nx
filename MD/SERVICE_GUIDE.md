# Systemd Service Guide - English Companion NX

Complete guide for running English Companion NX as a systemd service for 24/7 operation.

---

## 📋 Quick Start

### Installation

```bash
cd ~/apps/english-companion-nx
./scripts/install_service.sh
```

### Basic Commands

```bash
# Start the service
systemctl --user start english-companion-nx

# Stop the service
systemctl --user stop english-companion-nx

# Check status
systemctl --user status english-companion-nx

# View live logs
journalctl --user -u english-companion-nx -f
```

---

## 📖 Service Configuration

### Service File Location

**Template:** `systemd/english-companion-nx.service`
**Installed:** `~/.config/systemd/user/english-companion-nx.service`

### Key Settings

```ini
[Service]
WorkingDirectory=%h/apps/english-companion-nx
Environment="PATH=.../.venv/bin:..."

# Memory limits (Jetson Orin NX 16GB - allocate 11GB max)
MemoryMax=11G
MemoryHigh=10G

# Auto-restart on failure
Restart=on-failure
RestartSec=10
```

### Memory Limits Explained

- **MemoryMax=11G** - Hard limit (service killed if exceeded)
- **MemoryHigh=10G** - Soft limit (triggers cleanup before hitting hard limit)

Why 11G? Jetson Orin NX has 16GB total:
- 3-5GB: Operating system + JetPack services
- 11GB: Available for English Companion NX
- Models loaded at startup stay in memory (Whisper + Ollama + TTS)

---

## 🚀 Service Management

### Start Service

```bash
systemctl --user start english-companion-nx
```

**What happens:**
1. Systemd activates virtual environment
2. Loads models (Whisper, TTS, connects to Ollama)
3. Initializes conversation manager + memory monitor
4. Starts conversation loop

### Stop Service

```bash
systemctl --user stop english-companion-nx
```

**What happens:**
1. Graceful shutdown initiated
2. Conversation logs flushed to disk
3. Final memory cleanup
4. Models unloaded from RAM

### Restart Service

```bash
systemctl --user restart english-companion-nx
```

**When to restart:**
- After pulling code updates from GitHub
- After modifying .env configuration
- If service becomes unresponsive (though auto-restart should handle this)

### Check Status

```bash
systemctl --user status english-companion-nx
```

**Output shows:**
- Active/Inactive/Failed status
- PID, memory usage, uptime
- Recent log entries (last 10 lines)

---

## 📊 Monitoring

### View Logs

```bash
# Live logs (follow mode)
journalctl --user -u english-companion-nx -f

# Last 100 lines
journalctl --user -u english-companion-nx -n 100

# Logs since boot
journalctl --user -u english-companion-nx -b

# Logs for specific time range
journalctl --user -u english-companion-nx --since "2025-01-15 10:00" --until "2025-01-15 11:00"

# Logs with priority (errors only)
journalctl --user -u english-companion-nx -p err
```

### Memory Monitoring

The service logs memory usage after each conversation:

```
💾 RAM: 6789/14892 MB (45.6%) | GPU: 2456/7654 MB (32.1%)
```

Watch for cleanup events:

```
🧹 Running memory cleanup...
✅ Cleanup complete (0.15s)
   Objects collected: 1247
   Memory freed: 234.5 MB
   RAM usage: 58.3% → 52.1%
```

### Check Resource Usage

```bash
# Memory usage
systemctl --user show english-companion-nx -p MemoryCurrent

# CPU time
systemctl --user show english-companion-nx -p CPUUsageNSec

# Restart count
systemctl --user show english-companion-nx -p NRestarts
```

---

## ⚙️ Auto-Start on Boot

### Enable Auto-Start

```bash
# Enable service
systemctl --user enable english-companion-nx

# Enable lingering (required for user services to start at boot)
sudo loginctl enable-linger $USER
```

**Result:** Service starts automatically when Jetson boots

### Disable Auto-Start

```bash
systemctl --user disable english-companion-nx
```

**Note:** Currently NOT recommended to enable auto-start because the prototype is interactive (Press Enter mode). Enable this after implementing Phase 2 (wake word detection) for true hands-free operation.

---

## 🔧 Troubleshooting

### Service Won't Start

**1. Check logs for errors:**
```bash
journalctl --user -u english-companion-nx -n 50
```

**Common issues:**
- Virtual environment not found
- Missing dependencies
- Ollama not running
- Audio device not available
- .env configuration errors

**2. Verify dependencies:**
```bash
cd ~/apps/english-companion-nx
source .venv/bin/activate
python -c "import whisper, torch; from TTS.api import TTS; print('✅ All imports OK')"
```

**3. Check Ollama status:**
```bash
systemctl status ollama
curl http://localhost:11434/api/tags
```

**4. Verify audio devices:**
```bash
arecord -l   # List recording devices
pactl list sinks short  # List playback devices
```

### Service Crashes/Restarts

**Check restart count:**
```bash
systemctl --user show english-companion-nx -p NRestarts
```

**Check for OOM (Out of Memory) kills:**
```bash
journalctl --user -u english-companion-nx | grep -i "memory\|oom\|killed"
```

**If memory is the issue:**
- Reduce model sizes (.env: `WHISPER_MODEL=small` instead of `medium`)
- Lower cleanup interval (memory.py: `cleanup_interval=5` instead of `10`)
- Check memory limits in service file

### Service Uses Too Much Memory

**1. Check current memory usage:**
```bash
systemctl --user status english-companion-nx | grep Memory
```

**2. Adjust memory limits:**
```bash
# Edit service file
nano ~/.config/systemd/user/english-companion-nx.service

# Lower limits if needed
MemoryMax=9G
MemoryHigh=8G

# Reload and restart
systemctl --user daemon-reload
systemctl --user restart english-companion-nx
```

**3. Enable more aggressive cleanup:**

Edit `src/core/memory.py`:
```python
self.memory_monitor = MemoryMonitor(
    warning_threshold=0.75,  # Lower from 0.85
    critical_threshold=0.85,  # Lower from 0.95
    cleanup_interval=5       # More frequent (was 10)
)
```

### Logs Too Verbose

**Filter by priority:**
```bash
# Errors only
journalctl --user -u english-companion-nx -p err

# Warnings and errors
journalctl --user -u english-companion-nx -p warning
```

**Adjust log level in .env:**
```bash
LOG_LEVEL=WARNING  # Default: INFO
```

---

## 📝 Configuration

### Environment Variables

Service loads configuration from `.env` file:

```bash
# Edit configuration
nano ~/apps/english-companion-nx/.env

# Restart service to apply changes
systemctl --user restart english-companion-nx
```

**Key settings:**
- `WHISPER_MODEL` - Model size (base/small/medium)
- `OLLAMA_MODEL` - LLM model (llama3.2:3b)
- `AUDIO_INPUT_DEVICE` - Microphone device
- `AUDIO_OUTPUT_DEVICE` - Speaker device
- `LOG_LEVEL` - Logging verbosity

### Service File Customization

**Edit service file:**
```bash
nano ~/.config/systemd/user/english-companion-nx.service
```

**Common customizations:**

**Change restart policy:**
```ini
[Service]
Restart=always          # Always restart (even on success)
Restart=on-failure      # Only restart on failure (default)
Restart=no              # Never restart
RestartSec=30           # Wait 30s before restart (default: 10s)
```

**Change priority:**
```ini
[Service]
Nice=-10    # Higher priority (use more CPU when needed)
Nice=10     # Lower priority (background task)
```

**Add email notifications on failure** (requires mail setup):
```ini
[Service]
OnFailure=status-email-user@%i.service
```

**After editing, reload:**
```bash
systemctl --user daemon-reload
systemctl --user restart english-companion-nx
```

---

## 🎯 Best Practices

### Development Workflow

**1. Test changes manually first:**
```bash
cd ~/apps/english-companion-nx
source .venv/bin/activate
python conversation_prototype.py
# Verify everything works
```

**2. Push to GitHub from dev machine:**
```bash
git add .
git commit -m "your changes"
git push origin main
```

**3. Pull and restart service on Jetson:**
```bash
cd ~/apps/english-companion-nx
git pull origin main
pip install -r requirements-jetson.txt  # If dependencies changed
systemctl --user restart english-companion-nx
```

**4. Check logs for issues:**
```bash
journalctl --user -u english-companion-nx -f
```

### Production Deployment

**For 24/7 operation (after Phase 2 - wake word):**

1. ✅ Test thoroughly in interactive mode
2. ✅ Implement wake word detection
3. ✅ Verify memory monitoring works over long sessions
4. ✅ Enable auto-start:
   ```bash
   systemctl --user enable english-companion-nx
   sudo loginctl enable-linger $USER
   ```
5. ✅ Monitor for 24-48 hours
6. ✅ Set up alerting (optional)

### Health Checks

**Daily checks:**
```bash
# Quick status
systemctl --user status english-companion-nx

# Memory health
journalctl --user -u english-companion-nx --since today | grep "memory\|cleanup"

# Error count
journalctl --user -u english-companion-nx --since today | grep -i error | wc -l
```

**Weekly checks:**
```bash
# Total conversations
journalctl --user -u english-companion-nx --since "1 week ago" | grep "Transcribed:" | wc -l

# Restart count
systemctl --user show english-companion-nx -p NRestarts

# Memory peak
journalctl --user -u english-companion-nx --since "1 week ago" | grep "Peak RAM"
```

---

## 🔗 Related Documentation

- **DEPLOYMENT_CHECKLIST.md** - Complete deployment guide
- **CLAUDE.md** - Project architecture and constraints
- **TROUBLESHOOTING_NUMPY.md** - Dependency issues
- **Rob next steps.md** - Phase roadmap

---

## 📞 Quick Reference Card

```bash
# Start/Stop/Restart
systemctl --user start english-companion-nx
systemctl --user stop english-companion-nx
systemctl --user restart english-companion-nx

# Status & Logs
systemctl --user status english-companion-nx
journalctl --user -u english-companion-nx -f

# Enable/Disable Auto-Start
systemctl --user enable english-companion-nx
systemctl --user disable english-companion-nx

# After Config Changes
systemctl --user daemon-reload
systemctl --user restart english-companion-nx

# After Code Updates
cd ~/apps/english-companion-nx && git pull
systemctl --user restart english-companion-nx
```

---

**Phase Status:**
✅ Phase 1 Complete (Modularization, Logging, Memory, Service)
⏳ Phase 2 Next (Wake Word Detection for true 24/7 operation)

**Last Updated:** 2025-01-15
