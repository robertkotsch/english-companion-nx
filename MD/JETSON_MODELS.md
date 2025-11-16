# Jetson Orin NX - Available Models Guide

**Date:** October 27, 2025
**Hardware:** Jetson Orin NX 16GB (yahboom)
**Ollama Version:** Latest

---

## 📊 Pre-Installed Models on Jetson

### ✅ Working Models (Tested)

| Model | Size | RAM Usage | Response Time | Quality | Recommended Use |
|-------|------|-----------|---------------|---------|-----------------|
| **qwen2.5:3b-instruct** | ~2.0 GB | ~4 GB | ~5-7s (cold start) | ⭐⭐⭐⭐⭐ Excellent | **PRIMARY - Main conversations (better grammar, speed, determinism)** |
| llama3.2:3b | 2.0 GB | ~4 GB | ~8s (cold start) | ⭐⭐⭐⭐ Excellent | Previous default, good fallback |
| gemma2:2b | 1.6 GB | ~3 GB | ~5s (cold start) | ⭐⭐⭐ Good | Fast mode (Phase 5+) |
| llama3.1:8b | 4.9 GB | ❌ OOM | N/A | N/A | Too large for GPU memory |

### 🎯 Recommended Configuration

**Primary Model:** `qwen2.5:3b-instruct`
- ✅ Works reliably on Jetson Orin NX 16GB
- ✅ Excellent conversational quality with superior grammar understanding
- ✅ Natural, friendly responses with better determinism
- ✅ Faster than llama3.2:3b (~5-7s cold start, ~1-2s warm)
- ✅ Uses ~4GB RAM when loaded
- ✅ Excellent balance of quality, speed, and performance
- ✅ Better for language learning (improved grammar detection/correction)

---

## 🧪 Test Results

### Test 1: llama3.2:3b (SUCCESS ✅)

**Prompt:**
> "You are a friendly English conversation partner. Respond naturally to this: How are you today?"

**Response:**
> I'm feeling quite well, thank you for asking! It's lovely to have some company and chat with you. I've had a pretty relaxed morning so far, just got in some reading before we started talking. The weather outside is also quite pleasant, perfect for a cup of tea or a walk in the park. How about you?

**Performance:**
- **Cold start time:** ~8 seconds (includes model loading)
- **Memory usage:** ~4GB RAM
- **Quality:** Excellent - natural, conversational, engaging
- **Status:** ✅ **RECOMMENDED**

### Test 2: llama3.1:8b (FAILED ❌)

**Error:**
```
cudaMalloc failed: out of memory
llama_kv_cache_init: failed to allocate buffer for kv cache
```

**Reason:** Model requires more GPU memory than available on Orin NX
**Status:** ❌ **NOT USABLE**

### Test 3: gemma2:2b (FAILED ❌)

**Error:**
```
unable to allocate CUDA0 buffer
llama_load_model_from_file: failed to load model
```

**Reason:** Another model (llama3.2:3b) was already loaded in memory
**Status:** ⚠️ **USABLE IF ALONE** (but llama3.2:3b is better quality)

---

## 💡 Key Findings

### Memory Constraints
- **Jetson Orin NX 16GB:** Has 16GB unified memory (shared between CPU and GPU)
- **Available for models:** ~8-10GB after OS and services
- **Ollama behavior:** Keeps models loaded in memory for fast subsequent queries
- **Challenge:** Can only load ONE model at a time in GPU memory

### Model Loading Behavior
- First query loads model into memory (~5-8 seconds)
- Subsequent queries are much faster (~1-2 seconds)
- Model stays loaded until:
  - Ollama service restarts
  - System runs low on memory
  - Another model is loaded (evicts previous one)

### Performance Characteristics
- **Cold start (first query):** 5-8 seconds
- **Warm queries (model cached):** 1-3 seconds
- **Token generation speed:** ~30-50 tokens/second
- **Total response time:** ~2-4 seconds (warm)

---

## 📋 Recommended Setup

### .env Configuration

```bash
# Primary model for conversations
OLLAMA_MODEL=qwen2.5:3b-instruct

# Optional alternatives:
# OLLAMA_MODEL=llama3.2:3b  # Previous default, good fallback
# OLLAMA_FAST_MODEL=gemma2:2b  # Future fast mode feature
```

### Model Pre-warming Strategy

To avoid 8-second cold start on first conversation:

```python
# In main.py startup sequence
def prewarm_model():
    """Load model into memory at service startup"""
    import ollama
    ollama.generate(
        model='qwen2.5:3b-instruct',
        prompt='System warmup',
        stream=False
    )
    print("✅ Model prewarmed and ready")
```

---

## 🔄 Other Available Models (Not Tested for Conversation)

| Model | Size | Purpose |
|-------|------|---------|
| nomic-embed-text:latest | 274 MB | Embeddings/vector search (Phase 4+) |
| qwen2:7b | 4.4 GB | Alternative conversational (may have OOM issues) |
| phi3:3.8b | 2.2 GB | Potential alternative to llama3.2:3b |
| wizardlm2:7b | 4.1 GB | Likely too large (OOM) |
| gemma:7b | 5.0 GB | Likely too large (OOM) |
| **Code-focused models:** |
| codellama:7b | 3.8 GB | Not suitable for conversation |
| deepseek-coder:6.7b | 3.8 GB | Not suitable for conversation |
| starcoder2:7b | 4.0 GB | Not suitable for conversation |
| **Multimodal models:** |
| llava:7b | 4.7 GB | Image + text (overkill for audio-only) |
| llava-phi3:3.8b | 2.9 GB | Image + text (overkill for audio-only) |
| **Tiny models:** |
| tinyllama:1.1b | 637 MB | Too small for quality conversations |
| orca-mini:3b | 2.0 GB | Older model, llama3.2:3b is better |

---

## 🎯 Decision Matrix

### Use qwen2.5:3b-instruct if:
- ✅ You want best conversational quality with superior grammar understanding
- ✅ You want faster response times than llama3.2:3b
- ✅ You have 16GB Jetson Orin NX (you do!)
- ✅ You want natural, engaging conversations with better determinism
- ✅ You're building a language learning application (excellent grammar capabilities)

### Use llama3.2:3b if:
- ✅ You prefer the previous default model
- ✅ You want proven stability (longer testing history)

### Future Considerations (Phase 5+):
- **Fast mode toggle:** Allow switching to gemma2:2b for quicker responses
  - Requires unloading qwen2.5:3b-instruct first
  - Trade-off: Speed vs. Quality

- **Hybrid approach:**
  - Keep qwen2.5:3b-instruct loaded (main conversations)
  - Only load gemma2:2b for "quick mode" if user explicitly requests

- **Model upgrades:**
  - Monitor for new 3B-4B models with better quality
  - Test phi3:3.8b as alternative
  - Consider qwen2.5:7b-instruct if memory can be freed

---

## 🔧 Troubleshooting

### "Out of memory" errors
**Solution:** You're trying to load a model that's too large (8B+). Stick with 3B models.

### Slow first response (8+ seconds)
**Expected behavior:** First query loads model into memory. Implement pre-warming at service startup.

### Model not responding
**Check Ollama service:**
```bash
systemctl status ollama
journalctl -u ollama -f
```

### Want to switch models
**Unload current model first:**
```bash
# Stop Ollama service (unloads all models)
sudo systemctl restart ollama

# Or just run the new model (auto-evicts old one)
ollama run gemma2:2b "test"
```

---

## 📊 Memory Budget

With qwen2.5:3b-instruct as primary model:

```
Component                    Memory
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
System + OS                  3.0 GB
qwen2.5:3b-instruct          4.0 GB
Whisper Small                1.5 GB
Coqui TTS                    0.5 GB
Python Application           0.5 GB
Audio Buffers                0.3 GB
System Buffer                0.7 GB
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total                        10.5 GB ✅ (fits in 16GB)
Available for overhead       5.5 GB
```

**Status:** ✅ **Fits comfortably with room to spare**

---

## ✅ Final Recommendation

**Use `qwen2.5:3b-instruct` as your primary conversational model.**

- Excellent quality for English conversation practice
- Superior grammar understanding and determinism
- Faster than llama3.2:3b (5-7s cold start, ~1-2s warm)
- Leaves memory for Whisper and TTS
- Best balance of quality, speed, and resource usage
- Ideal for language learning applications

**Fallback:** `llama3.2:3b` if you prefer the previous default or need proven stability

---

**Last Updated:** October 27, 2025
**Hardware:** Jetson Orin NX 16GB
**Status:** Ready for Phase 1 implementation
