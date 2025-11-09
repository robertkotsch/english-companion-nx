# Operations & Maintenance Guide

Complete guide for running, monitoring, and maintaining English Companion NX.

## Running the Voice Assistant

### Production Mode (Phase 2B - Always-On)

```bash
# On Jetson
cd ~/apps/english-companion-nx
source .venv/bin/activate
python voice_assistant.py
```

**What it does:**
1. Loads OpenWakeWord (dual model: "hey jarvis" + "alexa")
2. Loads Whisper (small), TTS (VITS), connects to Ollama
3. Detects audio device sample rate (16000 Hz for PowerConf S3)
4. Starts listening for wake word "hey jarvis"
5. When detected → starts conversation session
6. Generates greeting with LLM and speaks it
7. Multiple Q&A exchanges without repeating wake word
8. VAD auto-stops recording after 3s silence
9. Filters Whisper hallucinations ("you", etc.)
10. Auto-ends session after 30s idle timeout
11. Shows session summary
12. Returns to wake word listening

**Usage:**
- Say "hey jarvis" to start a conversation session
- Ask multiple questions naturally
- Pauses of 3+ seconds stop your recording
- Session auto-ends after 30s of inactivity
- Press Ctrl+C to exit

**Performance:** ~10-20s per exchange (varies by speech length)

### Testing Mode (Interactive)

```bash
# Press Enter mode (no wake word)
python conversation_prototype.py
```

**What it does:**
1. Loads models (Whisper, TTS, Ollama)
2. Press Enter to record 5 seconds of speech
3. Plays beep → start speaking
4. Single Q&A exchange per Enter press
5. No wake word, no sessions, no idle timeout

**Use for:** Testing individual components, debugging audio issues

## Service Management

### Basic Service Control

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

# View logs (since today)
journalctl --user -u english-companion-nx --since today

# View logs (specific time range)
journalctl --user -u english-companion-nx --since "2024-12-01 10:00" --until "2024-12-01 11:00"
```

### Enable/Disable Service

```bash
# Enable service (start on boot)
systemctl --user enable english-companion-nx

# Disable service
systemctl --user disable english-companion-nx

# Check if enabled
systemctl --user is-enabled english-companion-nx
```

## Model Management

### Ollama Models

```bash
# Pull models (one-time setup)
ollama pull llama3.2:3b
ollama pull llama3.1:13b-instruct-q4_0
ollama pull nomic-embed-text  # For future embeddings

# List installed models
ollama list

# Remove unused models
ollama rm <model-name>

# Check Ollama service status
systemctl status ollama

# Test Ollama connection
ollama run llama3.2:3b "Hello, how are you?"
```

### Model Locations

```
Whisper models:   ~/.cache/whisper/
TTS models:       ~/.local/share/tts/
OpenWakeWord:     Bundled in package
Ollama models:    /usr/share/ollama/.ollama/models/
```

## Testing Components

### Audio Hardware Tests

```bash
# Test microphone + speaker
python test_audio.py

# Test specific audio device
python test_audio.py --device 0

# List available audio devices
python -c "import pyaudio; p = pyaudio.PyAudio(); \
  [print(f'{i}: {p.get_device_info_by_index(i)[\"name\"]}') \
   for i in range(p.get_device_count())]; p.terminate()"
```

### Wake Word Tests

```bash
# Test wake word detection (30 seconds)
python test_wake_word.py basic 30

# Debug wake word with confidence scores
python debug_wake_word.py 30 hey_jarvis 0

# Test with custom threshold
python voice_assistant.py hey_jarvis alexa 0.3 0.5 0
```

### VAD Recording Tests

```bash
# Test VAD recording with silence detection
python test_vad_recording.py

# Test with custom parameters
python test_vad_recording.py --silence-threshold 0.02 --silence-duration 4.0
```

### Speech Component Tests

```bash
# Test TTS only
python test_tts.py

# Test individual components (if modules support)
python -m src.speech.transcription  # Test Whisper
python -m src.speech.synthesis      # Test TTS
python -m src.conversation.llm_client  # Test LLM
```

### Full Flow Tests

```bash
# Test full conversation flow
python test_conversation_flow.py

# Memory pressure test
python scripts/memory_pressure_test.py
```

## Monitoring

### System Resources

```bash
# Jetson stats (install: sudo pip3 install jetson-stats)
jtop

# Memory usage
free -h

# Detailed memory info
cat /proc/meminfo

# Top processes by memory
ps aux --sort=-%mem | head -n 10

# GPU memory usage
nvidia-smi
```

### Temperature Monitoring

```bash
# Check all thermal zones
cat /sys/class/thermal/thermal_zone*/temp

# Continuous monitoring
watch -n 1 'cat /sys/class/thermal/thermal_zone*/temp'

# Check specific zone
cat /sys/class/thermal/thermal_zone0/temp

# Display in Celsius
cat /sys/class/thermal/thermal_zone0/temp | awk '{print $1/1000 "°C"}'
```

### SSD Health

```bash
# Check SMART data
sudo smartctl -a /dev/nvme0n1

# Check percentage used
sudo smartctl -a /dev/nvme0n1 | grep "Percentage Used"

# Check data units written
sudo smartctl -a /dev/nvme0n1 | grep "Data Units Written"

# Full health test
sudo smartctl -t short /dev/nvme0n1
```

### Disk Usage

```bash
# Check disk usage
du -sh ~/apps/english-companion-nx/*

# Check logs size
du -sh ~/apps/english-companion-nx/logs

# Check tmpfs usage
df -h /tmp

# Check conversation data
du -sh ~/companion-data/
```

### Conversation Stats

```bash
# View conversation stats (when implemented)
python scripts/conversation_stats.py

# Count total conversations
wc -l ~/companion-data/conversations.jsonl

# Recent conversations
tail -n 20 ~/companion-data/conversations.jsonl
```

### Network Monitoring

```bash
# Check listening ports
sudo ss -ltnp | grep -E "8000|8001|11434"

# Check Ollama service
curl http://localhost:11434/api/tags

# Test network connectivity
ping -c 3 google.com
```

## Maintenance

### Log Management

```bash
# Rotate logs manually
sudo logrotate -f /etc/logrotate.d/english-companion-nx

# Check log rotation config
cat /etc/logrotate.d/english-companion-nx

# Clear old journal logs (keeps last 7 days)
sudo journalctl --vacuum-time=7d

# Clear old journal logs (keeps max 500M)
sudo journalctl --vacuum-size=500M
```

### Cleanup Operations

```bash
# Clean old conversations (keeps last 30 days)
python scripts/cleanup_old_conversations.py --days 30

# Clean tmpfs (should auto-cleanup)
rm -f /tmp/companion-audio/*

# Clean Python cache
find ~/apps/english-companion-nx -type d -name __pycache__ -exec rm -rf {} +
find ~/apps/english-companion-nx -type f -name "*.pyc" -delete

# Clean pip cache
pip cache purge
```

### Backup Operations

```bash
# Backup conversations
python scripts/backup_conversations.py

# Manual backup
cp ~/companion-data/conversations.jsonl ~/backups/conversations-$(date +%Y%m%d).jsonl

# Backup configuration
cp .env ~/backups/env-$(date +%Y%m%d).backup

# Full backup to remote
rsync -avz ~/companion-data/ user@backup-server:/backups/companion-nx/
```

### Updates & Upgrades

```bash
# Update code from git
cd ~/apps/english-companion-nx
git pull origin main

# Update Python dependencies
source .venv/bin/activate
pip install --upgrade -r requirements-jetson.txt

# Update Ollama models
ollama pull llama3.2:3b

# System updates
sudo apt update && sudo apt upgrade -y

# Restart service after update
systemctl --user restart english-companion-nx
```

## Health Checks

### Daily Health Check Script

```bash
#!/bin/bash
# ~/apps/english-companion-nx/scripts/daily_health_check.sh

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
du -sh ~/companion-data/
```

### Schedule in Crontab

```bash
# Edit crontab
crontab -e

# Add daily health check (runs at 2 AM)
0 2 * * * ~/apps/english-companion-nx/scripts/daily_health_check.sh >> ~/health_checks.log

# Add weekly backup (runs Sunday at 3 AM)
0 3 * * 0 ~/apps/english-companion-nx/scripts/backup_conversations.py

# Add monthly cleanup (runs 1st of month at 4 AM)
0 4 1 * * ~/apps/english-companion-nx/scripts/cleanup_old_conversations.py --days 90
```

## Prometheus Metrics

### Exposed Metrics

```
# Available on http://localhost:8001/metrics

# Counters
companion_conversations_total           # Total conversations
companion_model_loads_total             # Model loading count

# Gauges
companion_memory_bytes                  # Current memory usage
companion_temperature_celsius           # System temperature
companion_response_time_seconds         # Latest response time

# Histograms
companion_transcription_duration_seconds  # Whisper timing
companion_llm_generation_duration_seconds # LLM timing
companion_tts_synthesis_duration_seconds  # TTS timing
```

### Query Metrics

```bash
# Fetch all metrics
curl http://localhost:8001/metrics

# Specific metric
curl http://localhost:8001/metrics | grep companion_conversations_total
```

## Best Practices Checklist

### Startup Checklist
- [ ] Models loaded once (Whisper, LLM, TTS)
- [ ] tmpfs directory created (/tmp/companion-audio)
- [ ] Conversation logger initialized with buffering
- [ ] Memory guard activated
- [ ] Thermal monitor started
- [ ] Prometheus metrics server started

### During Operation Checklist
- [ ] Audio recordings to tmpfs only
- [ ] Conversation logs buffered (5-min flush)
- [ ] Context pruned (last 20 exchanges max)
- [ ] Garbage collection every 10 conversations
- [ ] Memory checked before heavy operations
- [ ] Temperature monitored every 30s

### Maintenance Checklist
- [ ] Daily health check runs (cron)
- [ ] Logs rotated (weekly)
- [ ] Old conversations archived (monthly)
- [ ] SSD health checked (weekly)
- [ ] Backups created (weekly)
- [ ] System updates applied (monthly)

---

**Last Updated:** December 2024
