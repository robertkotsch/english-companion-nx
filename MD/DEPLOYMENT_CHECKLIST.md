# Deployment Checklist - Jetson Orin NX

## Pre-Deployment (Dev Machine)

### 1. Code Ready
- [ ] All changes committed to git
- [ ] Tests pass locally (if applicable)
- [ ] Documentation updated (CLAUDE.md, README.md)
- [ ] Pushed to GitHub: `git push origin main`

### 2. Configuration
- [ ] .env.example updated with new variables
- [ ] No secrets in .env.example
- [ ] WHISPER_MODEL set to `small` (not `medium` - memory constraints)

## Deployment (On Jetson)

### 3. Pull Latest Code
```bash
cd ~/apps/english-companion-nx
git pull origin main
```

### 4. Setup/Update Virtual Environment

**First time setup:**
```bash
# Create venv with system-site-packages (for NVIDIA PyTorch)
python3 -m venv .venv --system-site-packages
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies (use FIXED version!)
pip install -r requirements-jetson.txt

# Run numpy fix if needed
./fix_numpy_jetson.sh
```

**Updates (existing venv):**
```bash
source .venv/bin/activate

# Update dependencies
pip install -r requirements-jetson.txt

# If you see numpy downgrade, run fix:
./fix_numpy_jetson.sh
```

### 5. Configure Environment
```bash
# Copy example if .env doesn't exist
cp .env.example .env

# Edit configuration
nano .env

# Key settings to check:
# - WHISPER_MODEL=small (NOT medium - memory!)
# - AUDIO_INPUT_DEVICE=plughw:0,0 (verify with: arecord -l)
# - AUDIO_OUTPUT_DEVICE=alsa_output... (verify with: pactl list sinks short)
# - OLLAMA_MODEL=llama3.2:3b (verify with: ollama list)

# Secure .env
chmod 600 .env
```

### 6. Verify Models

```bash
# Check Ollama models
ollama list

# Pull if missing
ollama pull llama3.2:3b

# Verify Ollama running
systemctl status ollama
```

### 7. Create Required Directories

```bash
# Create data directories
mkdir -p ~/companion-data/logs
mkdir -p /tmp/companion-audio

# Verify tmpfs (should already exist)
df -h /tmp | grep tmpfs
```

### 8. Test Installation

```bash
# Activate venv
source .venv/bin/activate

# Test imports
python -c "import numpy; print('numpy:', numpy.__version__)"
# Should show: numpy: 1.24.x or higher (NOT 1.22.0!)

python -c "import whisper; print('whisper: OK')"
python -c "from TTS.api import TTS; print('TTS: OK')"
python -c "import torch; print('PyTorch CUDA:', torch.cuda.is_available())"
# Should show: PyTorch CUDA: True

# Check all dependencies
pip check
# Should show: No broken requirements found.

# Test audio hardware
python test_audio.py

# Test TTS
python test_tts.py
```

### 9. Test Prototype

```bash
# Run interactive mode
python conversation_prototype.py

# Expected flow:
# 1. Models load (Whisper, TTS connect to Ollama)
# 2. Press Enter → beep → speak for 5 seconds
# 3. Transcription appears
# 4. LLM response generated
# 5. TTS speech plays through speaker
# 6. Repeat

# Verify performance:
# - Transcription: ~1-2s
# - LLM generation: ~6-8s
# - TTS synthesis: ~2.5s
# - Total: ~12-15s per exchange
```

## Troubleshooting

### Common Issues

**Problem: "numpy 1.22.0 is incompatible"**
```bash
source .venv/bin/activate
./fix_numpy_jetson.sh
# See QUICK_FIX_NUMPY.md for details
```

**Problem: "Device or resource busy" (audio)**
```bash
# Kill orphan arecord processes
pkill -9 arecord

# Or restart prototype (has built-in cleanup)
python conversation_prototype.py
```

**Problem: "CUDA out of memory"**
```bash
# Use Whisper 'small' instead of 'medium'
nano .env
# Change: WHISPER_MODEL=small

# Restart prototype
python conversation_prototype.py
```

**Problem: "Ollama connection refused"**
```bash
# Check Ollama service
systemctl status ollama

# Start if needed
sudo systemctl start ollama

# Verify model loaded
ollama list
```

**Problem: First word cut off in transcription**
- This is expected behavior (buffer warmup trimming)
- The code automatically trims 1.0s from start of recording
- Includes beep, so user speech starts after trim point

**Problem: TTS audio clips at start**
- Fixed in current version (0.5s silence padding)
- If still occurs, check AUDIO_OUTPUT_DEVICE in .env

## Post-Deployment Verification

### 10. Monitor Resources

```bash
# Check memory usage
free -h
# Should have ~2-3GB free after model loading

# Check temperature
cat /sys/class/thermal/thermal_zone0/temp
# Should be <70000 (70°C) under normal operation

# Check disk usage
df -h ~
df -h /tmp

# Check SSD health (if concerned)
sudo smartctl -a /dev/nvme0n1 | grep "Percentage Used"
```

### 11. Run for Extended Period

```bash
# Test stability (run 10+ conversations)
python conversation_prototype.py

# Monitor memory over time
# Should stay stable (no leaks)

# Check logs
ls -lh ~/companion-data/logs/
```

## Production Deployment (Phase 1 Complete)

### 12. Setup Systemd Service (Future)

```bash
# Create service file
sudo nano /etc/systemd/user/english-companion-nx.service

# Enable and start
systemctl --user enable english-companion-nx
systemctl --user start english-companion-nx

# Check status
systemctl --user status english-companion-nx

# View logs
journalctl --user -u english-companion-nx -f
```

### 13. Enable Auto-Start on Boot (Future)

```bash
# Enable lingering (start user services at boot)
sudo loginctl enable-linger $USER
```

## Rollback Procedure

If deployment fails:

```bash
# 1. Check what changed
cd ~/apps/english-companion-nx
git log -1
git diff HEAD~1

# 2. Rollback to previous version
git reset --hard HEAD~1

# 3. Recreate venv if needed
rm -rf .venv
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
pip install -r requirements-jetson.txt

# 4. Restore .env if needed
cp .env.backup .env

# 5. Test
python conversation_prototype.py
```

## Maintenance

### Regular Checks (Weekly)

```bash
# Update from git
cd ~/apps/english-companion-nx
git pull origin main

# Update dependencies (if requirements changed)
source .venv/bin/activate
pip install -r requirements-jetson.txt

# Check logs
ls -lh ~/companion-data/logs/

# Check SSD health
sudo smartctl -a /dev/nvme0n1 | grep "Percentage Used"
```

### Backup (Weekly)

```bash
# Backup conversations (when implemented)
cp ~/companion-data/conversations.jsonl ~/backups/conversations_$(date +%Y%m%d).jsonl

# Backup .env
cp ~/apps/english-companion-nx/.env ~/backups/env_backup
```

## Success Criteria

- [ ] `pip check` shows no conflicts
- [ ] `python -c "import numpy; print(numpy.__version__)"` shows >=1.24
- [ ] All test scripts pass (test_audio.py, test_tts.py)
- [ ] conversation_prototype.py runs without errors
- [ ] Audio recording works (can hear beep, transcription accurate)
- [ ] LLM responses generated successfully
- [ ] TTS speech plays clearly through speaker
- [ ] No memory errors after 10+ conversations
- [ ] Temperature stays <70°C during operation

---

**Last Updated:** 2025-10-31
**Current Phase:** Phase 1 Prototype
