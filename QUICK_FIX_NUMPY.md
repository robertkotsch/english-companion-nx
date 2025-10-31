# Quick Fix: Numpy Downgrade Issue on Jetson

## The Problem

After running `pip install -r requirements-jetson.txt`, numpy gets downgraded from 1.26.4 to 1.22.0, breaking system packages (jax, tensorflow, chex, ultralytics).

## Quick Fix (Run on Jetson)

### Option 1: Automated Fix Script (Recommended)

```bash
cd ~/apps/english-companion-nx
source .venv/bin/activate
./fix_numpy_jetson.sh
```

### Option 2: Manual Fix (Fast)

```bash
cd ~/apps/english-companion-nx
source .venv/bin/activate

# Force upgrade numpy
pip install --upgrade --force-reinstall 'numpy>=1.24.1,<2.0.0'

# Verify
python -c "import numpy; print('numpy:', numpy.__version__)"
# Should show: numpy: 1.24.x or higher (NOT 1.22.0)

# Check for conflicts
pip check
```

### Option 3: Reinstall in Correct Order

```bash
cd ~/apps/english-companion-nx
source .venv/bin/activate

# Install numpy first (establishes constraint)
pip install 'numpy>=1.24.1,<2.0.0'

# Then TTS (has many dependencies)
pip install TTS>=0.21.0

# Then Whisper
pip install openai-whisper>=20231117

# Finally, everything else
pip install -r requirements-jetson.txt

# Verify
pip check
```

### Option 4: Use Fixed Requirements File

```bash
cd ~/apps/english-companion-nx
source .venv/bin/activate

# Use the fixed version that installs numpy first
pip install -r requirements-jetson.txt

# Verify
pip check
```

## Verify the Fix

```bash
# 1. Check numpy version (should be >=1.24)
python -c "import numpy; print('numpy:', numpy.__version__)"

# 2. Check all dependencies
pip check

# 3. Test imports
python -c "import whisper; print('whisper OK')"
python -c "from TTS.api import TTS; print('TTS OK')"
python -c "import torch; print('CUDA:', torch.cuda.is_available())"

# 4. Test the prototype
python conversation_prototype.py
```

## If Still Broken

See **TROUBLESHOOTING_NUMPY.md** for:
- Strategy 3: Switch to faster-whisper (alternative to openai-whisper)
- Strategy 4: Recreate venv from scratch
- Detailed diagnosis steps

## Root Cause

**openai-whisper** has a transitive dependency that forces old numpy. JetPack system packages (jax, tensorflow, etc.) need numpy>=1.24.

**Solution:** Install numpy **first** to establish the version constraint before other packages.

## Prevention

Use **requirements-jetson.txt** which installs numpy first:

```txt
# CRITICAL: Install numpy FIRST to prevent downgrades
numpy>=1.24.1,<2.0.0

# Then other packages...
openai-whisper>=20231117
TTS>=0.21.0
# ...
```

---

**Last Updated:** 2025-10-31
