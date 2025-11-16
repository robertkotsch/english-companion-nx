# Troubleshooting Guide

Complete troubleshooting guide for English Companion NX (Phase 2B).

## Wake Word Detection Issues

### Problem: Wake word not detecting

**Cause:** Audio device issues, wrong sample rate, or threshold too strict

**Solution:**
```bash
# Test wake word separately
python test_wake_word.py basic 30

# Debug with confidence scores
python debug_wake_word.py 30 hey_jarvis 0

# Try lower threshold (0.3 instead of 0.5)
python voice_assistant.py hey_jarvis alexa 0.3 0.5 0
```

### Problem: Multiple detections for single wake word

**Cause:** Cooldown too short

**Solution:** Increase cooldown in `src/audio/wake_word.py:137` from 2.0s to 3.0s

```python
# In wake_word.py
if time.time() - self.last_detection_time < 3.0:  # Changed from 2.0
    return WakeWordType.NONE
```

### Problem: ALSA warnings at startup

```
ALSA lib pcm.c:2660:(snd_pcm_open_noupdate) Unknown PCM cards.pcm.rear
ALSA lib pcm.c:2660:(snd_pcm_open_noupdate) Unknown PCM cards.pcm.center_lfe
Cannot find card '1'
```

**Cause:** PyAudio probes all possible devices including non-existent ones

**Solution:** Harmless! These warnings appear once during sample rate auto-detection, then stop. No action needed.

## Audio Device Conflicts

### Problem: "No supported sample rate found for device"

**Cause:** Wake word detector holds audio device open, VAD recording can't access it

**Solution:** Stop wake detector before VAD recording, restart after:

```python
self.wake_detector.stop()        # Free audio device
audio_file = self.recorder.record_with_vad(...)  # Now can record
self.wake_detector.start()       # Resume wake word detection
```

See `voice_assistant.py:118-122` for reference implementation.

### Problem: "Device or resource busy" error

**Cause:** Previous audio process still running

**Solution:** Handled automatically by `cleanup_previous_instances()` on startup. If persists:

```bash
# Kill zombie processes
pkill -9 arecord
pkill -9 python

# Restart
python voice_assistant.py
```

### Problem: "Jack server is not running" warning

**Cause:** JACK audio server not installed/running

**Solution:** Harmless if using ALSA/PulseAudio. Ignore or install JACK:

```bash
sudo apt-get install jackd2
```

## VAD Recording Issues

### Problem: Recording cuts off my speech

**Cause:** Silence duration too short (stops recording too quickly)

**Solution:** Increase from 3.0s to 4.0s or 5.0s in `voice_assistant.py:125`:

```python
silence_duration=4.0,  # Give yourself more time to think
```

### Problem: Recording doesn't stop (hits 30s max duration)

**Cause:** Silence threshold too low (background noise counted as speech)

**Solution:** Increase from 0.01 to 0.02 or 0.03 in `voice_assistant.py:124`:

```python
silence_threshold=0.02,  # Less sensitive to background noise
```

### Problem: First word of speech cut off

**Cause:** ALSA buffer initialization lag (Phase 1 issue, should be fixed)

**Solution:** Already handled by VAD recording (no trimming needed). If persists, increase pre-recording buffer in `recorder.py`.

### Problem: No audio input detected

**Cause:** Wrong audio device or permissions

**Solution:**

```bash
# List audio devices
python test_audio.py

# Check device permissions
ls -l /dev/snd/*

# Test specific device
python test_vad_recording.py --device 0

# Check PulseAudio
pactl list sources short
```

## Session Management Issues

### Problem: Session times out too quickly

**Cause:** Idle timeout too short

**Solution:** Increase from 30s to 60s in `voice_assistant.py:278`:

```python
def run_conversation_session(self, idle_timeout: float = 60.0):
```

### Problem: Session won't timeout (idle for >30s but still active)

**Cause:** Whisper hallucinations reset idle timer

**Solution:** Already fixed! Hallucinations filtered and ignored (don't reset timer). Check `voice_assistant.py:165-168` for implementation.

### Problem: Greeting not visible/audible

**Cause:** Error in greeting generation or TTS

**Solution:** Already fixed! Greeting always displays, errors handled separately. Check logs for TTS/playback errors:

```bash
journalctl --user -u english-companion-nx -n 100 | grep -i "greeting\|tts"
```

### Problem: Session doesn't start after wake word

**Cause:** Audio device conflict or wake detector not stopping

**Solution:** Check logs for errors. Ensure wake detector stops properly:

```bash
journalctl --user -u english-companion-nx -f
```

## Whisper Transcription Issues

### Problem: Whisper outputs "you" during silence

**Cause:** Known Whisper hallucination

**Solution:** Already filtered! System ignores "you", "thank you", "okay", etc. See `voice_assistant.py:157-163` for filter implementation.

### Problem: Transcription takes too long (>3s)

**Cause:** Using wrong Whisper model size or CPU instead of GPU

**Solution:** Verify using Whisper small on GPU:

```bash
# Check in initialization logs
python voice_assistant.py 2>&1 | grep -i "whisper\|device"

# Should see:
# "Loading Whisper model: small"
# "Device: CUDA"
```

### Problem: "RuntimeError: CUDA out of memory"

**Cause:** Whisper model too large or GPU memory fragmented

**Solution:**

```python
# Use smaller model
WHISPER_MODEL=base  # Instead of small or medium

# Clear GPU cache
import torch
torch.cuda.empty_cache()
```

### Problem: Poor transcription accuracy

**Cause:** Background noise, wrong language, or unclear speech

**Solution:**

```bash
# Test in quiet environment
python test_vad_recording.py

# Check language setting in config
cat .env | grep WHISPER

# Ensure using English model
WHISPER_LANGUAGE=en
```

## Model/Memory Issues

### Problem: Ollama returns "Out of memory" error

**Cause:** Whisper medium + LLM (qwen2.5:3b-instruct or llama3.2:3b) exceeds 16GB RAM

**Solution:** Use Whisper small instead (already default in Phase 2B)

```bash
# Edit .env
WHISPER_MODEL=small  # Not medium

# Check current memory usage
free -h
```

### Problem: "module 'coverage' has no attribute 'types'"

**Cause:** Old coverage 6.x, numba needs 7.x

**Solution:**

```bash
source .venv/bin/activate
pip install --upgrade coverage
```

### Problem: Whisper using CPU instead of GPU

**Cause:** venv missing system PyTorch

**Solution:** Recreate venv with `--system-site-packages`:

```bash
cd ~/apps/english-companion-nx
rm -rf .venv
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
pip install -r requirements-jetson.txt
```

### Problem: Memory keeps increasing (memory leak)

**Cause:** Models not being released or context growing unbounded

**Solution:**

```bash
# Check for leaks
python scripts/memory_leak_detector.py

# Ensure periodic cleanup
# Check voice_assistant.py:210-215 for gc.collect()
```

## Dependency Issues

### Problem: "No module named 'openwakeword'"

**Cause:** OpenWakeWord not installed

**Solution:**

```bash
source .venv/bin/activate
pip install openwakeword
```

### Problem: TTS import fails with "No module named 'torchaudio'"

**Cause:** torchaudio not installed or version mismatch

**Solution:**

```bash
# Build from source
cd ~/torchaudio
git checkout v2.5.0  # Match PyTorch version
USE_CUDA=0 pip install . --no-build-isolation
```

### Problem: PyAudio build failed "portaudio.h: No such file or directory"

**Cause:** Missing system library

**Solution:**

```bash
sudo apt-get update
sudo apt-get install -y portaudio19-dev
pip install pyaudio
```

### Problem: "ImportError: libcudnn.so.8: cannot open shared object file"

**Cause:** Missing CUDA libraries

**Solution:**

```bash
# Check CUDA installation
nvidia-smi
nvcc --version

# Install missing libraries
sudo apt-get install -y libcudnn8 libcudnn8-dev

# Add to LD_LIBRARY_PATH
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH
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

# Monitor memory
watch -n 1 free -h
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
sudo ss -ltnp | grep 11434

# 4. Permission issues
ls -la .env  # Should be 600
ls -la /tmp/companion-audio  # Should be writable

# Manual start (debug mode)
cd ~/apps/english-companion-nx
source .venv/bin/activate
python voice_assistant.py  # See errors directly
```

### SSD Health Degradation

```bash
# Check SMART data
sudo smartctl -a /dev/nvme0n1 | grep -E "Percentage Used|Data Units Written"

# If >70% wear:
# 1. Backup conversations
python scripts/backup_conversations.py --destination /backup/

# 2. Reduce write frequency (increase buffer)
# Edit .env: CONVERSATION_BUFFER_INTERVAL=600  # 10 minutes

# 3. Plan SSD replacement
# 4. Continue monitoring weekly

# If >90% wear:
# URGENT: Replace SSD immediately
# Order replacement and schedule maintenance
```

### Corrupted Conversation Log

```bash
# Validate JSONL file
python -c "import json; \
  with open('~/companion-data/conversations.jsonl') as f: \
    [json.loads(line) for line in f]"

# If corrupted, restore from backup
cp ~/backups/conversations-latest.jsonl ~/companion-data/conversations.jsonl

# If no backup, rebuild from journal logs
python scripts/rebuild_conversation_log.py
```

### Ollama Service Down

```bash
# Check Ollama status
systemctl status ollama

# Restart Ollama
sudo systemctl restart ollama

# Check if models loaded
ollama list

# Test connection
curl http://localhost:11434/api/tags

# If still down, check logs
journalctl -u ollama -n 100
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

# Test with topic integration (Phase 3+)
python test_with_mcp.py
```

## Debugging Tips

### Enable Debug Logging

```bash
# Edit .env
LOG_LEVEL=DEBUG

# Restart service
systemctl --user restart english-companion-nx

# View debug logs
journalctl --user -u english-companion-nx -f
```

### Capture Audio for Analysis

```bash
# Modify recorder.py to save audio files
# Comment out cleanup in voice_assistant.py:145

# Files saved to /tmp/companion-audio/
# Analyze with:
ffprobe /tmp/companion-audio/recording_*.wav
```

### Profile Performance

```bash
# Run with profiler
python -m cProfile -o profile.stats voice_assistant.py

# Analyze profile
python -c "import pstats; \
  p = pstats.Stats('profile.stats'); \
  p.sort_stats('cumulative').print_stats(20)"
```

---

**Last Updated:** December 2024
