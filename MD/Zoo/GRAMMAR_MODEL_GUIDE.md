# GrammarGiraffe Model Comparison Guide

Test and compare different LLM models for grammar detection.

---

## Available Models

### llama3.2:3b (Current Default)
- **Size:** ~2GB RAM
- **Speed:** ~500ms per utterance
- **Accuracy:** Good for basic errors
- **Issues:** Struggles with complex structures, high false positive rate for subject-verb and prepositions

### llama3.2:8b (Recommended for Better Accuracy)
- **Size:** ~5GB RAM
- **Speed:** ~1-1.5s per utterance
- **Accuracy:** Much better at complex grammar, fewer false positives
- **Requirements:** More RAM (may be tight on Jetson)

---

## Quick Start

### On Jetson - Download the 8B Model

```bash
# Download llama3.2:8b (this may take a few minutes, ~5GB download)
ollama pull llama3.2:8b

# Verify it's available
ollama list
```

### Test Both Models

```bash
# Run comparison test
python3 tests/test_grammar_models.py
```

**This will:**
- Test 8 different utterances (correct and incorrect grammar)
- Compare accuracy between 3b and 8b models
- Show false positive and false negative rates
- Recommend which model to use

---

## Using Different Models

### In Interactive Test

```bash
# Use default 3b model
python3 tests/test_zoo_interactive.py

# Use 8b model for better accuracy
python3 tests/test_zoo_interactive.py --grammar-model llama3.2:8b
```

### In Your Code

```python
from src.zoo.listeners import GrammarGiraffe

# Default (3b model)
grammar = GrammarGiraffe()

# Use 8b model
config = {'llm_model': 'llama3.2:8b'}
grammar = GrammarGiraffe(config)
```

---

## Memory Considerations (Jetson Orin NX 16GB)

### Current Usage with 3B Model:
```
Phase 2B base:     ~8GB  (Whisper, Ollama 3b, TTS, wake word)
Zoo overhead:      ~0.4GB
─────────────────────────
Total:             ~8.4GB / 11GB usable
Headroom:          ~2.6GB
```

### With 8B Model:
```
Phase 2B base:     ~11GB  (Whisper, Ollama 8b, TTS, wake word)
Zoo overhead:      ~0.4GB
─────────────────────────
Total:             ~11.4GB / 11GB usable
Headroom:          <0.5GB ⚠️ TIGHT!
```

**Note:** You may need to ensure only one model is loaded at a time.

---

## Expected Improvements with 8B Model

### Test Cases from Real Usage:

**1. "Either you run your life, or life runs you"**
- **3B model:** Flags as error (severity 0.90, false positive)
- **8B model:** Likely recognizes as correct ✓

**2. "What are the tools I would be using?"**
- **3B model:** Flags as error (severity 0.70, false positive)
- **8B model:** Likely recognizes as correct ✓

**3. "This is an nice example"**
- **3B model:** Detects (severity 0.70, correct)
- **8B model:** Detects with higher confidence ✓

### Category-Specific Improvements:

The 8B model should significantly improve:
- **Subject-verb detection** - Fewer false positives
- **Prepositions** - Better understanding of conjunctions vs prepositions
- **Complex structures** - "Either...or", "Neither...nor", etc.

---

## Threshold Adjustments for 8B Model

If using 8B model, you can use **stricter (lower) thresholds**:

```python
config = {
    'llm_model': 'llama3.2:8b',
    'category_thresholds': {
        'articles': 0.5,         # Keep strict
        'pluralization': 0.6,    # Keep strict
        'pronouns': 0.6,         # Keep strict
        'tense': 0.6,            # Lowered from 0.7
        'subject_verb': 0.7,     # Lowered from 0.95 (more reliable with 8b)
        'word_order': 0.6,       # Lowered from 0.7
        'prepositions': 0.7,     # Lowered from 0.95 (more reliable with 8b)
    }
}

grammar = GrammarGiraffe(config)
```

---

## Performance Trade-offs

### Speed Comparison:
| Model | Utterance Processing | Acceptable? |
|-------|---------------------|-------------|
| 3b | ~500ms | ✓ Fast |
| 8b | ~1000-1500ms | ✓ Still acceptable for async |

**Note:** In Phase 1.5, GrammarGiraffe runs in background while user is speaking/thinking, so 1-1.5s is acceptable.

---

## Recommended Configuration by Use Case

### Development/Testing (Relaxed)
```python
config = {
    'llm_model': 'llama3.2:3b',  # Fast for iteration
    'min_severity': 0.3,         # See everything
}
```

### Production - Balanced (Default)
```python
config = {
    'llm_model': 'llama3.2:3b',      # Lower memory
    'category_thresholds': {         # Strict thresholds
        'subject_verb': 0.95,
        'prepositions': 0.95,
        # ... (current defaults)
    }
}
```

### Production - High Accuracy
```python
config = {
    'llm_model': 'llama3.2:8b',      # Better accuracy
    'category_thresholds': {         # Can use lower thresholds
        'subject_verb': 0.7,
        'prepositions': 0.7,
        # ... (relaxed from 0.95)
    }
}
```

---

## Testing Checklist

Before deploying 8B model:

- [ ] Download model: `ollama pull llama3.2:8b`
- [ ] Run comparison: `python3 tests/test_grammar_models.py`
- [ ] Check accuracy improvement
- [ ] Monitor memory usage: `free -h`
- [ ] Test interactive: `python3 tests/test_zoo_interactive.py --grammar-model llama3.2:8b`
- [ ] Verify speed is acceptable (~1-1.5s)
- [ ] Ensure only one model loaded: `ollama ps`

---

## Switching Models in Production

### Option 1: Environment Variable (Planned)

```bash
# In .env file
ZOO_GRAMMAR_MODEL=llama3.2:8b
```

### Option 2: Direct Configuration

```python
# In voice_assistant_zoo.py
grammar_config = {
    'llm_model': os.getenv('ZOO_GRAMMAR_MODEL', 'llama3.2:3b')
}
grammar_listener = GrammarGiraffe(grammar_config)
```

---

## Troubleshooting

### Model Not Found
```
Error: model 'llama3.2:8b' not found
```

**Solution:**
```bash
ollama pull llama3.2:8b
```

### Out of Memory
```
Error: failed to allocate memory
```

**Solution:**
```bash
# Ensure only one model loaded
ollama ps

# If 3b is running, stop it
ollama stop llama3.2:3b

# Or restart ollama service
sudo systemctl restart ollama
```

### Slow Performance
```
Grammar analysis taking >2s
```

**Check:**
- CPU/GPU utilization: `nvidia-smi`
- Other processes: `top`
- Model size: Ensure using intended model `ollama ps`

---

## Future Options

Other models to consider:

- **llama3.1:8b** - Alternative 8B model
- **llama3.2:13b** - Even better accuracy (if memory allows)
- **mistral:7b** - Good alternative to llama3.2:8b
- **phi3:medium** - Microsoft's efficient model

Test any model with:
```bash
ollama pull <model-name>
python3 tests/test_zoo_interactive.py --grammar-model <model-name>
```

---

## See Also

- `test_grammar_models.py` - Automated comparison script
- `test_zoo_interactive.py` - Interactive testing with model selection
- `PHASE_1.2_SUMMARY.md` - GrammarGiraffe implementation details
