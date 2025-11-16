# Jetson Orin NX Setup Guide

**Hardware:** Jetson Orin NX 16GB
**OS:** JetPack 6.x (Ubuntu 22.04)
**Python:** 3.10.12

---

## ⚠️ Important: Dependency Installation Order

The Jetson has **pre-installed packages** from NVIDIA that you should NOT reinstall. Follow this exact order:

### Step 1: Verify Pre-installed Packages

```bash
# Check PyTorch (should already be installed)
python3 -c "import torch; print(f'PyTorch: {torch.__version__}, CUDA: {torch.cuda.is_available()}')"

# Expected output:
# PyTorch: 2.x.x, CUDA: True
```

**If PyTorch is not installed or CUDA doesn't work:**
- You may need to reinstall JetPack or follow NVIDIA's PyTorch installation guide
- DO NOT use `pip install torch` - use NVIDIA's wheel files

### Step 2: Create Virtual Environment

```bash
cd ~/apps/english-companion-nx

# Create venv
python3 -m venv .venv

# Activate
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### Step 3: Install Dependencies (Jetson-specific)

```bash
# Use Jetson-specific requirements file
pip install -r requirements-jetson.txt
```

**If you get errors:**
- Try installing packages one by one
- Some packages may need system dependencies (see below)

---

## 📦 System Dependencies

Some Python packages need system libraries:

```bash
# Audio libraries (for pyaudio)
sudo apt-get update
sudo apt-get install -y portaudio19-dev python3-pyaudio

# For soundfile
sudo apt-get install -y libsndfile1

# For OpenCV (if needed by Whisper/TTS)
sudo apt-get install -y python3-opencv

# Build tools (if compiling from source)
sudo apt-get install -y build-essential
```

---

## 🎯 Phase-by-Phase Installation

Don't install everything at once. Install only what you need for each phase:

### Phase 1: Basic Setup + LLM

```bash
pip install ollama python-dotenv psutil requests pydantic
```

**Test:**
```bash
python3 << EOF
import ollama
print("Ollama:", ollama.__version__)
EOF
```

### Phase 2: Add Whisper (Speech-to-Text)

```bash
# Install Whisper
pip install openai-whisper

# This will install numpy, torch dependencies automatically
```

**Test:**
```bash
python3 << EOF
import whisper
model = whisper.load_model("base")
print("Whisper loaded successfully!")
EOF
```

**Note:** First time will download the model (~140MB for base, ~1.5GB for medium)

### Phase 3: Add TTS (Text-to-Speech)

**Option A: Simple TTS (Recommended for testing)**
```bash
pip install pyttsx3
```

**Option B: Coqui TTS (Better quality, more complex)**
```bash
# Warning: This has many dependencies and may conflict
pip install TTS

# If conflicts, try:
pip install TTS --no-deps
# Then manually install missing dependencies
```

### Phase 4: Add Audio I/O

```bash
# Install system dependencies first
sudo apt-get install -y portaudio19-dev

# Then install Python packages
pip install pyaudio soundfile
```

---

## 🔍 Troubleshooting

### Problem: "No module named 'torch'"

**Solution:** PyTorch not installed or venv can't see system PyTorch
```bash
# Option 1: Use system site-packages
python3 -m venv .venv --system-site-packages

# Option 2: Install PyTorch wheel for Jetson
# Follow: https://forums.developer.nvidia.com/t/pytorch-for-jetson/
```

### Problem: "numpy version conflict"

**Solution:** Let packages resolve their own numpy dependencies
```bash
# Uninstall all
pip uninstall numpy torch openai-whisper TTS -y

# Reinstall in order (without version pinning)
pip install numpy
pip install openai-whisper
pip install TTS
```

### Problem: "pyaudio installation fails"

**Solution:** Install system dependencies first
```bash
sudo apt-get install -y portaudio19-dev python3-dev
pip install pyaudio
```

### Problem: "TTS installation takes forever / fails"

**Solution:** TTS has heavy dependencies. Consider alternatives:
```bash
# Option 1: Use simpler TTS for Phase 1-2
pip install pyttsx3

# Option 2: Skip TTS entirely for now, test with text output
# Add TTS in Phase 3 when core conversation works
```

---

## ✅ Verify Installation

After installing packages, verify they work:

```bash
python3 << 'EOF'
print("=== Checking Installations ===")

try:
    import torch
    print(f"✅ PyTorch {torch.__version__} (CUDA: {torch.cuda.is_available()})")
except ImportError as e:
    print(f"❌ PyTorch: {e}")

try:
    import whisper
    print(f"✅ Whisper {whisper.__version__}")
except ImportError as e:
    print(f"❌ Whisper: {e}")

try:
    import ollama
    print(f"✅ Ollama {ollama.__version__}")
except ImportError as e:
    print(f"❌ Ollama: {e}")

try:
    import pyaudio
    print(f"✅ PyAudio")
except ImportError as e:
    print(f"❌ PyAudio: {e}")

try:
    from dotenv import load_dotenv
    print(f"✅ python-dotenv")
except ImportError as e:
    print(f"❌ python-dotenv: {e}")

print("\n=== Configuration ===")
import psutil
mem = psutil.virtual_memory()
print(f"RAM: {mem.total // (1024**3)}GB total, {mem.available // (1024**3)}GB available")

EOF
```

---

## 🎯 Recommended Installation Strategy

**For initial setup (right now):**

```bash
# Minimal installation for testing
pip install ollama python-dotenv psutil requests

# Test Ollama connection
python3 -c "import ollama; print(ollama.list())"
```

**This gets you:**
- ✅ LLM connectivity (qwen2.5:3b-instruct recommended, or llama3.2:3b)
- ✅ Configuration management (.env files)
- ✅ System monitoring
- ✅ Ready to test basic conversation flow

**Add Whisper and TTS later** when you're ready to implement audio pipeline (Phase 2).

---

## 📝 Current Status

Based on your Jetson:
- ✅ Python 3.10.12
- ✅ Ollama installed and working
- ✅ qwen2.5:3b-instruct model (or llama3.2:3b)
- ✅ Repository cloned
- ⏭️ Virtual environment created
- ⏭️ Dependencies to install

**Next Step:** Install minimal dependencies for Phase 1

```bash
source .venv/bin/activate
pip install -r requirements-jetson.txt
```

---

**Last Updated:** October 27, 2025
**Status:** Ready for dependency installation
