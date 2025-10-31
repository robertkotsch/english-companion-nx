# Numpy Dependency Conflict - Troubleshooting Guide

## Problem Summary

During `pip install -r requirements-jetson.txt` on Jetson Orin NX, numpy gets downgraded from 1.26.4 to 1.22.0, causing dependency conflicts:

```
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed.
This behaviour is the source of the following dependency conflicts.
chex 0.1.88 requires numpy>=1.24.1, but you have numpy 1.22.0 which is incompatible.
jax 0.4.34 requires numpy>=1.24, but you have numpy 1.22.0 which is incompatible.
jaxlib 0.4.34 requires numpy>=1.24, but you have numpy 1.22.0 which is incompatible.
tensorflow-cpu-aws 2.15.1 requires numpy>=1.23.5,<2.0.0, but you have numpy 1.22.0 which is incompatible.
ultralytics 8.3.65 requires numpy>=1.23.0, but you have numpy 1.22.0 which is incompatible.
```

## Root Cause Analysis

### Likely Culprit: openai-whisper

Openai-whisper has a known issue where it pins an old numpy version in some installations. The package may have a transitive dependency that forces numpy<1.23.

### Why These Packages Are Present

The packages mentioned (chex, jax, jaxlib, tensorflow-cpu-aws, ultralytics) are likely:
1. **Pre-installed on JetPack** (NVIDIA's software stack)
2. **Dependencies of TTS** (Coqui TTS has heavy ML dependencies)
3. **Dependencies of openai-whisper** (may pull in JAX for some operations)

## Diagnosis Steps (Run on Jetson)

### 1. Check what's forcing old numpy

```bash
# Activate venv
cd ~/apps/english-companion-nx
source .venv/bin/activate

# Show what requires numpy
pip show numpy

# Check dependency tree
pip install pipdeptree
pipdeptree -p numpy
pipdeptree -r -p numpy  # Reverse: what depends on numpy

# Check what installed numpy 1.22.0
pip list | grep numpy
```

### 2. Check system packages

```bash
# Check if these packages came from JetPack
python3 -c "import sys; print(sys.path)"

# List packages from system-site-packages
pip list --user
pip list | grep -E "jax|tensorflow|chex|ultralytics"
```

### 3. Identify the conflict source

```bash
# Check each requirement individually
pip install --dry-run openai-whisper
pip install --dry-run TTS
pip install --dry-run pyaudio
```

## Solution Strategies

### Strategy 1: Force numpy Upgrade (Quick Fix)

```bash
cd ~/apps/english-companion-nx
source .venv/bin/activate

# Try to upgrade numpy explicitly
pip install --upgrade 'numpy>=1.24.1,<2.0.0'

# If that fails, try forcing reinstall
pip install --force-reinstall 'numpy>=1.24.1,<2.0.0'

# Verify all packages are satisfied
pip check
```

**If this works:** Update requirements-jetson.txt to pin numpy explicitly.

### Strategy 2: Install in Correct Order (Recommended)

The issue might be installation order. Install heavy dependencies first:

```bash
cd ~/apps/english-companion-nx
source .venv/bin/activate

# Install numpy explicitly first
pip install 'numpy>=1.24.1,<2.0.0'

# Install TTS (has heavy dependencies)
pip install TTS>=0.21.0

# Then install Whisper
pip install openai-whisper>=20231117

# Then install remaining packages
pip install -r requirements-jetson.txt
```

### Strategy 3: Use faster-whisper Instead (Alternative)

OpenAI Whisper has known dependency issues. Consider switching to faster-whisper:

```bash
# Uninstall openai-whisper
pip uninstall openai-whisper

# Install faster-whisper (better maintained, faster, fewer conflicts)
pip install faster-whisper>=1.0.0
```

**Note:** This requires code changes in `conversation_prototype.py`.

### Strategy 4: Create Fresh venv (Nuclear Option)

If all else fails, recreate the virtual environment:

```bash
cd ~/apps/english-companion-nx

# Backup .env if it exists
cp .env .env.backup 2>/dev/null || true

# Remove old venv
rm -rf .venv

# Create new venv with system-site-packages
python3 -m venv .venv --system-site-packages

# Activate
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install numpy first
pip install 'numpy>=1.24.1,<2.0.0'

# Install requirements in order
pip install TTS>=0.21.0
pip install openai-whisper>=20231117
pip install -r requirements-jetson.txt

# Verify
pip check
python -c "import numpy; print('numpy version:', numpy.__version__)"
python -c "import whisper; print('whisper OK')"
python -c "import TTS; print('TTS OK')"
```

## Permanent Fix: Update requirements-jetson.txt

Once you find the working configuration, update requirements:

```txt
# Jetson Orin NX - Compatible Dependencies
# Python 3.10.12 on JetPack 6.x

# Core AI/ML Components
# NOTE: PyTorch comes pre-installed with JetPack - DO NOT REINSTALL

# CRITICAL: Install numpy first to prevent downgrades
numpy>=1.24.1,<2.0.0  # Required by jax, tensorflow, chex, ultralytics

# Speech-to-text (choose one)
openai-whisper>=20231117  # Original (may have dependency issues)
# faster-whisper>=1.0.0  # Alternative (recommended, fewer conflicts)

# Text-to-Speech
TTS>=0.21.0  # Coqui TTS (has many dependencies)

# ... rest of requirements ...
```

## Verification Tests

After fixing, run these tests on Jetson:

```bash
# 1. Check all dependencies satisfied
pip check

# 2. Check numpy version
python -c "import numpy; print('numpy:', numpy.__version__)"
# Should print: numpy: 1.24.x or 1.26.x

# 3. Test Whisper
python -c "import whisper; model = whisper.load_model('tiny'); print('Whisper OK')"

# 4. Test TTS
python -c "from TTS.api import TTS; print('TTS OK')"

# 5. Test PyTorch with CUDA
python -c "import torch; print('CUDA available:', torch.cuda.is_available())"
# Should print: CUDA available: True

# 6. Run the prototype
python conversation_prototype.py
# Should load models and start interactive mode
```

## Why This Happened

### JetPack System Packages

NVIDIA JetPack comes with pre-installed ML packages optimized for Jetson:
- TensorFlow (tensorflow-cpu-aws)
- JAX/Jaxlib (for hardware acceleration)
- Ultralytics (YOLO for computer vision)
- Various CUDA-optimized libraries

These are installed **system-wide** and are accessible via `--system-site-packages`.

### The Conflict

When you run `pip install -r requirements-jetson.txt`:
1. Pip installs packages in order
2. Some package (likely openai-whisper or its dependency) requires old numpy
3. Pip downgrades numpy to satisfy that requirement
4. This breaks system packages that need numpy>=1.24

### The Solution

**Install numpy first and explicitly** before other packages to establish the constraint.

## Alternative: Isolate from System Packages

If you want to **avoid** system package conflicts entirely:

```bash
# Create venv WITHOUT --system-site-packages
python3 -m venv .venv  # No --system-site-packages flag

# Install PyTorch manually (from NVIDIA)
# Follow: https://forums.developer.nvidia.com/t/pytorch-for-jetson/72048

# Then install requirements
pip install -r requirements-jetson.txt
```

**Downside:** You lose access to NVIDIA's optimized PyTorch. You'll need to install everything manually.

## Quick Commands Reference

```bash
# Activate venv
cd ~/apps/english-companion-nx && source .venv/bin/activate

# Check numpy version
python -c "import numpy; print(numpy.__version__)"

# Force upgrade numpy
pip install --upgrade --force-reinstall 'numpy>=1.24.1,<2.0.0'

# Check all dependencies
pip check

# Show dependency tree
pip install pipdeptree && pipdeptree -p numpy

# List what depends on numpy (reverse)
pipdeptree -r -p numpy

# Test critical imports
python -c "import whisper, TTS, torch; print('All OK')"
```

## Expected Working Configuration

After fix, `pip list` should show:

```
numpy                 1.24.x or 1.26.x  (NOT 1.22.0)
openai-whisper        20231117 or later
TTS                   0.21.x or later
torch                 2.5.0 (from JetPack)
torchaudio            2.x.x (built from source)
chex                  0.1.88
jax                   0.4.34
jaxlib                0.4.34
tensorflow-cpu-aws    2.15.1
ultralytics           8.3.65
```

All packages should be satisfied with no conflicts.

## Contact Info

If none of these work, gather this info and ask for help:

```bash
# Python version
python3 --version

# Pip version
pip --version

# System packages
pip list | grep -E "numpy|jax|tensorflow|whisper|TTS|torch"

# Dependency tree
pipdeptree -p numpy

# Installation log
pip install -r requirements-jetson.txt 2>&1 | tee install.log
# Then share install.log
```

---

**Last Updated:** 2025-10-31
**Status:** Active troubleshooting
