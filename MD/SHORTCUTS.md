# Quick Shortcuts Reference

Quick reference for all English Companion NX command shortcuts.

## Setup

Run this once on your Jetson to add all shortcuts:

```bash
cd ~/apps/english-companion-nx
bash setup_alias.sh
source ~/.bashrc
```

## Available Shortcuts

### 🏠 Navigation & Activation

| Shortcut | Command | Description |
|----------|---------|-------------|
| `ec` | `cd ~/apps/english-companion-nx && source .venv/bin/activate` | Go to project and activate venv |
| `ecrun` | `cd ~/apps/english-companion-nx && source .venv/bin/activate && python voice_assistant.py` | Run voice assistant directly |

**Usage examples:**
```bash
# SSH in, then just type:
ec

# Or run the assistant directly:
ecrun
```

### 🔧 Service Control

| Shortcut | Command | Description |
|----------|---------|-------------|
| `ecstart` | `systemctl --user start english-companion-nx` | Start the service |
| `ecstop` | `systemctl --user stop english-companion-nx` | Stop the service |
| `ecrestart` | `systemctl --user restart english-companion-nx` | Restart the service |
| `ecstatus` | `systemctl --user status english-companion-nx` | View service status |
| `eclogs` | `journalctl --user -u english-companion-nx -f` | View service logs (live) |

**Usage examples:**
```bash
# Stop running service
ecstop

# Update code
ecupdate

# Restart service with new code
ecrestart

# Watch logs live
eclogs
```

### 🔄 Updates & Testing

| Shortcut | Command | Description |
|----------|---------|-------------|
| `ecupdate` | `cd ~/apps/english-companion-nx && git pull` | Git pull latest changes |
| `ectest` | `cd ~/apps/english-companion-nx && source .venv/bin/activate && python tests/test_audio.py` | Test audio hardware |
| `ecwake` | `cd ~/apps/english-companion-nx && source .venv/bin/activate && python tests/test_wake_word.py basic 30` | Test wake word detection (30s) |

**Usage examples:**
```bash
# Pull latest code
ecupdate

# Test audio after reboot
ectest

# Test wake word sensitivity
ecwake
```

### 📊 Monitoring

| Shortcut | Command | Description |
|----------|---------|-------------|
| `ecmem` | `free -h && echo "" && nvidia-smi` | View memory & GPU usage |
| `ectemp` | `cat /sys/class/thermal/thermal_zone*/temp \| awk '{print $1/1000"°C"}'` | View CPU/GPU temperatures |

**Usage examples:**
```bash
# Check if running out of memory
ecmem

# Check if overheating
ectemp
```

## Common Workflows

### Quick Test After Changes

```bash
# SSH into Jetson
ssh jetson@your-jetson

# Pull latest code
ecupdate

# Test it
ecrun
```

### Service Management

```bash
# Deploy new version
ecstop
ecupdate
ecrestart

# Watch logs to verify it works
eclogs
```

### Debugging Issues

```bash
# Check service status
ecstatus

# View recent logs
eclogs

# Check memory usage
ecmem

# Check temperatures
ectemp

# Test audio hardware
ectest

# Test wake word
ecwake
```

## Removing Shortcuts

If you want to remove these shortcuts, edit `~/.bashrc` and delete the section:

```bash
nano ~/.bashrc

# Find and delete the section:
# ═══════════════════════════════════════════════════════
# English Companion NX - Quick Shortcuts
# ═══════════════════════════════════════════════════════
# ... (all the aliases) ...

# Then reload:
source ~/.bashrc
```

## Adding Custom Shortcuts

You can add your own custom shortcuts to `~/.bashrc`:

```bash
# Example: Quick restart with logs
alias ecrl='ecrestart && sleep 2 && eclogs'

# Example: Full system check
alias eccheck='ecstatus && echo "" && ecmem && echo "" && ectemp'
```

---

**Tip:** Type `alias | grep ec` to see all available ec* shortcuts at any time.
