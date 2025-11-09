# Installation Guide - Jetson Orin NX

## Quick Installation

Due to numpy dependency conflicts between Coqui TTS and JetPack system packages, follow this **three-step installation process**:

### Step 1: Install Main Dependencies

```bash
cd ~/apps/english-companion-nx
source .venv/bin/activate
pip install -r requirements-jetson.txt
```

This installs all dependencies **except TTS**.

### Step 2: Install TTS with Dependency Override

```bash
pip install TTS==0.22.0 --no-deps
```

The `--no-deps` flag bypasses TTS's strict `numpy==1.22.0` requirement, allowing it to use JetPack's `numpy>=1.24.1`. TTS works correctly with numpy 1.24+ despite the declared dependency.

### Step 3: Download OpenWakeWord Models

```bash
python3 -c "import openwakeword; openwakeword.utils.download_models()"
```

This downloads the pre-trained wake word models (hey_jarvis, alexa, hey_mycroft, timer) to the OpenWakeWord package directory. Models are ~1-5MB each.

### Verify Installation

Test TTS functionality:

```bash
python test_tts.py
```

Test wake word detection:

```bash
python test_wake_word.py basic 30
```

Test full conversation system:

```bash
python conversation_prototype.py
```

## Why This Workaround is Needed

### The Problem

- **JetPack system packages** (jax, tensorflow, ultralytics, chex) require `numpy>=1.24.1`
- **Coqui TTS 0.20.x-0.22.x** requires `numpy==1.22.0` for Python 3.10
- These requirements are **mutually exclusive** → pip cannot resolve dependencies

### The Solution

Installing TTS with `--no-deps`:
- ✅ Allows TTS to use existing `numpy>=1.24.1` from JetPack
- ✅ TTS functions correctly with numpy 1.24+ (tested and working)
- ✅ Avoids downgrading numpy (which would break JetPack packages)
- ✅ All TTS dependencies are already installed via requirements-jetson.txt

### What Gets Skipped

When using `--no-deps`, TTS's numpy dependency check is bypassed, but:
- numpy is **already installed** (from requirements-jetson.txt line 6)
- All other TTS dependencies are **already installed** (librosa, inflect, etc.)
- TTS code is **compatible** with numpy 1.24+ despite the declared requirement

## Alternative: Use pyttsx3 (Simpler TTS)

If you prefer to avoid the TTS dependency workaround, you can use `pyttsx3` instead:

```bash
pip install pyttsx3
```

**Trade-offs:**
- ✅ No dependency conflicts
- ✅ Simpler installation
- ✅ Works offline
- ❌ Lower voice quality than Coqui TTS
- ❌ No GPU acceleration
- ❌ Limited voice customization

To switch to pyttsx3, modify `conversation_prototype.py` to use pyttsx3 instead of TTS.

## Troubleshooting

### "ImportError: numpy.core.multiarray failed to import"

**Cause:** numpy version mismatch
**Solution:** Ensure numpy 1.24.1+ is installed:
```bash
pip install --upgrade "numpy>=1.24.1,<2.0.0"
```

### "ModuleNotFoundError: No module named 'TTS'"

**Cause:** TTS not installed or step 2 was skipped
**Solution:** Run step 2:
```bash
pip install TTS==0.22.0 --no-deps
```

### TTS model download fails

**Cause:** Network issues or disk space
**Solution:** Manually download model:
```bash
tts --text "Test" --model_name "tts_models/en/ljspeech/vits" --out_path test.wav
```

### Audio playback issues

**Cause:** PulseAudio device misconfiguration
**Solution:** Check audio devices:
```bash
pactl list sinks
python test_audio.py
```

### "Could not open .tflite" - OpenWakeWord models not found

**Cause:** OpenWakeWord models not downloaded
**Solution:** Download models (step 3):
```bash
python3 -c "import openwakeword; openwakeword.utils.download_models()"
```

To verify models are downloaded:
```bash
python3 -c "import openwakeword; from openwakeword.model import Model; m = Model(); print('Available models:', list(m.models.keys()))"
```

### "GPU device discovery failed" warning (ONNX Runtime)

**Cause:** ONNX Runtime can't detect GPU on Jetson
**Solution:** This is a harmless warning. OpenWakeWord will use TFLite runtime (default on Linux) which works correctly with Jetson GPU. You can ignore this message.

## Full Clean Installation

If you encounter persistent issues, perform a clean installation:

```bash
cd ~/apps/english-companion-nx
deactivate  # Exit venv if active

# Remove existing venv
rm -rf .venv

# Create fresh venv with system site packages (for NVIDIA PyTorch)
python3 -m venv .venv --system-site-packages
source .venv/bin/activate

# Install dependencies (three-step process)
pip install --upgrade pip
pip install -r requirements-jetson.txt
pip install TTS==0.22.0 --no-deps
python3 -c "import openwakeword; openwakeword.utils.download_models()"

# Verify installation
python test_tts.py
python test_wake_word.py basic 30
python test_audio.py
python conversation_prototype.py
```

## Development Installation

For development with additional tools:

```bash
# After completing steps 1 & 2 above:
pip install pytest pytest-asyncio black ruff ipython
```

## See Also

- [JETSON_SETUP.md](MD/JETSON_SETUP.md) - Complete Jetson setup guide
- [CLAUDE.md](CLAUDE.md) - Development guidelines
- [README.md](README.md) - Project overview
