# Numpy Dependency Fix - Summary

## What Happened

During `pip install -r requirements-jetson.txt` on your Jetson Orin NX, numpy was downgraded from 1.26.4 to 1.22.0, causing conflicts with JetPack system packages.

## Root Cause

**openai-whisper** has a transitive dependency that forces an old numpy version (<1.23). However, NVIDIA JetPack pre-installs several packages that require numpy>=1.24:

- **chex 0.1.88** requires numpy>=1.24.1
- **jax 0.4.34** requires numpy>=1.24
- **jaxlib 0.4.34** requires numpy>=1.24
- **tensorflow-cpu-aws 2.15.1** requires numpy>=1.23.5,<2.0.0
- **ultralytics 8.3.65** requires numpy>=1.23.0

When pip installs requirements in order, it satisfies openai-whisper's old numpy requirement first, then complains about breaking system packages.

## Solution Strategy

**Install numpy FIRST** to establish the version constraint before other packages can downgrade it.

## Files Created

### 1. **QUICK_FIX_NUMPY.md** (Start Here!)
Quick reference with copy-paste commands for the most common fixes:
- Automated fix script
- Manual force upgrade
- Reinstall in correct order
- Use fixed requirements file

**Use this when:** You just want to fix the issue fast.

### 2. **TROUBLESHOOTING_NUMPY.md** (Deep Dive)
Comprehensive troubleshooting guide with:
- Root cause analysis
- Diagnosis commands
- 4 solution strategies
- Alternative approaches (faster-whisper, fresh venv)
- Verification tests

**Use this when:** Quick fix didn't work or you want to understand the issue.

### 3. **fix_numpy_jetson.sh** (Automated Fix)
Bash script that:
- Checks current numpy version
- Analyzes dependency tree
- Forces numpy upgrade
- Reinstalls in correct order if needed
- Verifies all imports work
- Color-coded output for easy reading

**Use this when:** You want an automated solution.

### 4. **requirements-jetson.txt** (Prevention)
Updated requirements file that:
- Installs numpy **first** (establishes constraint)
- Includes comments explaining why
- Suggests faster-whisper as alternative

**Use this when:** Setting up fresh or preventing future issues.

### 5. **DEPLOYMENT_CHECKLIST.md** (Production Guide)
Complete deployment checklist covering:
- Pre-deployment steps (dev machine)
- Deployment steps (Jetson)
- Configuration verification
- Testing procedures
- Troubleshooting common issues
- Success criteria

**Use this when:** Deploying to Jetson or setting up from scratch.

## Updated Files

### .env.example
- Changed `WHISPER_MODEL=medium` → `WHISPER_MODEL=small`
- Added note about numpy conflicts
- References TROUBLESHOOTING_NUMPY.md

**Reason:** Whisper small uses less memory and has fewer dependency issues than medium.

### Rob next steps.md
- Added "Known Issue: Numpy Dependency Conflict" section
- Links to quick fix documentation
- Explains root cause and prevention

## Quick Start (On Jetson)

### Option 1: Automated (Recommended)
```bash
cd ~/apps/english-companion-nx
source .venv/bin/activate
./fix_numpy_jetson.sh
```

### Option 2: Manual Fast Fix
```bash
cd ~/apps/english-companion-nx
source .venv/bin/activate
pip install --upgrade --force-reinstall 'numpy>=1.24.1,<2.0.0'
pip check
```

### Option 3: Fresh Install
```bash
cd ~/apps/english-companion-nx
source .venv/bin/activate
pip install -r requirements-jetson.txt
```

## Verification

After any fix, verify success:

```bash
# 1. Check numpy version (should be >=1.24)
python -c "import numpy; print('numpy:', numpy.__version__)"

# 2. Check all dependencies satisfied
pip check

# 3. Test imports
python -c "import whisper; print('whisper OK')"
python -c "from TTS.api import TTS; print('TTS OK')"
python -c "import torch; print('CUDA:', torch.cuda.is_available())"

# 4. Run prototype
python conversation_prototype.py
```

## Prevention (Future)

**Use requirements-jetson.txt instead of requirements-jetson.txt**

This file installs numpy first, preventing the downgrade:

```txt
# CRITICAL: Install numpy FIRST to prevent downgrades
numpy>=1.24.1,<2.0.0

# Then other packages...
openai-whisper>=20231117
TTS>=0.21.0
```

## Alternative Solutions (If Nothing Works)

### 1. Switch to faster-whisper
Openai-whisper has known dependency issues. faster-whisper is:
- Better maintained
- Faster inference
- Fewer dependency conflicts
- **Requires code changes** (different API)

### 2. Recreate venv from scratch
Sometimes a fresh start is needed:
```bash
rm -rf .venv
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
pip install -r requirements-jetson.txt
```

## Next Steps

1. **Deploy the fix files to Jetson:**
   ```bash
   # On dev machine
   git add .
   git commit -m "fix: Add numpy dependency conflict resolution"
   git push origin main

   # On Jetson
   cd ~/apps/english-companion-nx
   git pull origin main
   ```

2. **Run the fix:**
   ```bash
   source .venv/bin/activate
   ./fix_numpy_jetson.sh
   ```

3. **Verify and test:**
   ```bash
   pip check
   python conversation_prototype.py
   ```

4. **Continue with Phase 1:**
   Once numpy is fixed, you can proceed with:
   - Conversation logging (buffered JSONL)
   - Systemd service setup
   - Memory monitoring

## Questions?

- **Quick fix:** See QUICK_FIX_NUMPY.md
- **Deep troubleshooting:** See TROUBLESHOOTING_NUMPY.md
- **Deployment guide:** See DEPLOYMENT_CHECKLIST.md
- **Understanding the issue:** Read "Root Cause" section above

---

**Files Created:** 5 new, 2 updated
**Total Time:** ~30 minutes of diagnosis + documentation
**Status:** Ready for deployment and testing
**Last Updated:** 2025-10-31
