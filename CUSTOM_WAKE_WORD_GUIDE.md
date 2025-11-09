# Custom Wake Word Guide

**Create your own wake word instead of "hey jarvis"**

You have three options, ranked from easiest to most advanced.

---

## Option 1: Use Different Built-in Model (5 minutes) ⭐ EASIEST

OpenWakeWord includes several pre-trained models:

### Available Models

| Model | Wake Word | Best For |
|-------|-----------|----------|
| `hey_jarvis` | "hey jarvis" | Current default |
| `alexa` | "alexa" | Amazon-style |
| `hey_mycroft` | "hey mycroft" | Privacy-focused assistant |
| `timer` | "timer" | Short single word |

### How to Use

**Method 1: Command line argument**
```bash
cd ~/apps/english-companion-nx
source .venv/bin/activate

# Use "hey mycroft" instead of "hey jarvis"
python voice_assistant.py hey_mycroft alexa 0.5 0.5 0
```

**Method 2: Edit configuration**

Create or edit `.env`:
```bash
# Default wake word models
WAKE_WORD_START=hey_mycroft
WAKE_WORD_STOP=alexa
```

Then run normally:
```bash
python voice_assistant.py
```

---

## Option 2: Download Pre-Trained Custom Models (30 minutes) ⭐ RECOMMENDED

The OpenWakeWord community has created many custom models you can download and use directly.

### Step 1: Browse Available Models

Visit the OpenWakeWord model repository:
https://github.com/dscripka/openWakeWord/tree/main/openwakeword/models

Or the Hugging Face collection:
https://huggingface.co/davidscripka/openWakeWord

**Popular custom models:**
- "hey computer"
- "ok robot"
- "listen up"
- And many more!

### Step 2: Download Model

```bash
cd ~/apps/english-companion-nx

# Create models directory
mkdir -p custom_models

# Download a model (example: "hey computer")
wget -O custom_models/hey_computer.tflite \
  https://github.com/dscripka/openWakeWord/raw/main/openwakeword/models/hey_computer.tflite
```

### Step 3: Test the Model

```bash
python3 -c "
from src.audio.wake_word import WakeWordDetector

detector = WakeWordDetector(
    start_model='custom_models/hey_computer.tflite',
    start_threshold=0.5
)
detector.start()

print('Say: hey computer')
result = detector.detect_once(timeout=30)
print(f'Result: {result}')

detector.stop()
"
```

### Step 4: Use in Voice Assistant

**Method 1: Command line**
```bash
python voice_assistant.py custom_models/hey_computer.tflite alexa 0.5 0.5 0
```

**Method 2: Modify voice_assistant.py**

Edit `voice_assistant.py` line 484:
```python
# Before
wake_word_model = "hey_jarvis"

# After
wake_word_model = "custom_models/hey_computer.tflite"
```

---

## Option 3: Train Your Own Custom Model (2-4 hours) ⭐ ADVANCED

Train a completely custom wake word with ANY phrase you want!

### What You'll Need

- 20-50 recordings of your wake word (you saying it)
- Python environment with OpenWakeWord
- Patience for training process

### Method A: Google Teachable Machine (Easiest Training)

**Best for:** Quick custom models without coding

1. **Collect Samples**
   ```bash
   python train_custom_wake_word.py collect "hey companion" 30
   ```
   This records 30 samples of you saying "hey companion"

2. **Upload to Teachable Machine**
   - Go to: https://teachablemachine.withgoogle.com/train/audio
   - Create a new Audio Project
   - Class 1: Upload your wake word samples
   - Class 2: Background noise (record silence or ambient noise)
   - Train the model

3. **Export Model**
   - Export as: TensorFlow Lite
   - Download the `.tflite` file
   - Copy to `~/apps/english-companion-nx/custom_models/`

4. **Test and Use**
   ```bash
   python train_custom_wake_word.py test custom_models/hey_companion.tflite 30
   ```

### Method B: OpenWakeWord Training (Advanced)

**Best for:** Maximum control and quality

#### Step 1: Install Training Dependencies

```bash
cd ~/apps/english-companion-nx
source .venv/bin/activate
pip install openwakeword[train]
```

#### Step 2: Collect Training Data

```bash
# Collect 30 samples of your wake word
python train_custom_wake_word.py collect "hey companion" 30
```

**Result:** Audio files in `custom_wake_words/hey_companion/`

**Tips for good recordings:**
- Say the wake word naturally, as you would when using it
- Vary your tone slightly between samples
- Record in the same room/environment where you'll use it
- Keep background noise consistent

#### Step 3: Collect Negative Samples

You also need "negative" samples (things that are NOT your wake word):

```bash
# Record background noise and other speech
mkdir -p custom_wake_words/negatives

# Record 2-3 minutes of:
# - Silence
# - Normal conversation (not the wake word)
# - Background noise
# - Similar sounding phrases
```

#### Step 4: Prepare Training Data

Create a directory structure:
```
training_data/
├── positive/
│   └── [your wake word samples]
└── negative/
    └── [background noise, other speech]
```

```bash
mkdir -p training_data/positive training_data/negative

# Copy positive samples
cp custom_wake_words/hey_companion/*.wav training_data/positive/

# Copy negative samples
cp custom_wake_words/negatives/*.wav training_data/negative/
```

#### Step 5: Train the Model

```bash
# Using OpenWakeWord training script
python -m openwakeword.train \
    --positive_dir training_data/positive \
    --negative_dir training_data/negative \
    --output_model custom_models/hey_companion.tflite \
    --model_name "hey_companion" \
    --sample_rate 16000
```

**Training time:** 30 minutes - 2 hours depending on your hardware

#### Step 6: Test Your Model

```bash
python train_custom_wake_word.py test custom_models/hey_companion.tflite 30
```

Say your wake word multiple times to verify it works!

#### Step 7: Use Your Custom Model

```bash
python voice_assistant.py custom_models/hey_companion.tflite alexa 0.5 0.5 0
```

---

## Troubleshooting

### Model Not Detected

**Problem:** Wake word not detected reliably

**Solutions:**
1. **Lower threshold:**
   ```bash
   python voice_assistant.py hey_jarvis alexa 0.3 0.5 0  # Try 0.3 instead of 0.5
   ```

2. **Record more samples:** 50+ samples improve accuracy

3. **Check audio quality:** Ensure microphone is working well

### False Positives

**Problem:** Wake word triggers on similar sounds

**Solutions:**
1. **Raise threshold:**
   ```bash
   python voice_assistant.py hey_jarvis alexa 0.7 0.5 0  # Try 0.7 instead of 0.5
   ```

2. **Add more negative samples:** Include similar-sounding words in training

3. **Choose a more unique phrase:** "hey companion" is more unique than "hey"

### Model File Not Found

**Problem:** `FileNotFoundError` when loading custom model

**Solution:**
```bash
# Ensure model exists
ls -lh custom_models/

# Use absolute path
python voice_assistant.py /full/path/to/custom_models/hey_companion.tflite
```

---

## Recommendations

### For Quick Testing
**Use:** Built-in model like `hey_mycroft`
- No training required
- Works immediately
- Reliable performance

### For Production Use
**Use:** Pre-trained custom model from OpenWakeWord repository
- Community-tested
- Good accuracy
- Wide variety available

### For Personal/Unique Phrase
**Use:** Google Teachable Machine training
- Easy web interface
- Fast training (minutes)
- Good for unique phrases

### For Maximum Quality
**Use:** Full OpenWakeWord training pipeline
- Complete control
- Best accuracy
- Most time-intensive

---

## Performance Tips

### Optimal Wake Word Characteristics

**Good wake words:**
- ✅ 2-3 syllables ("hey jarvis", "computer")
- ✅ Distinct sounds (hard consonants)
- ✅ Unique to your environment
- ✅ Easy to pronounce naturally

**Avoid:**
- ❌ Single syllable ("go", "stop")
- ❌ Common words ("the", "and", "ok")
- ❌ Similar to background speech
- ❌ Hard to pronounce consistently

### Threshold Tuning

| Threshold | Sensitivity | False Positives | False Negatives |
|-----------|-------------|-----------------|-----------------|
| 0.3 | Very High | Many | Few |
| 0.5 | Balanced | Some | Some |
| 0.7 | Conservative | Few | More |
| 0.9 | Very Low | Rare | Many |

**Start with 0.5** and adjust based on your experience.

### Environment Considerations

- **Quiet room:** Can use lower threshold (0.4-0.5)
- **Noisy environment:** Use higher threshold (0.6-0.7)
- **Multiple speakers:** Train with all users' voices
- **Different rooms:** Collect samples in each location

---

## Examples

### Example 1: Switch to "hey mycroft"

```bash
cd ~/apps/english-companion-nx
source .venv/bin/activate
python voice_assistant.py hey_mycroft alexa 0.5 0.5 0
```

### Example 2: Use downloaded "hey computer" model

```bash
# Download model
wget -O custom_models/hey_computer.tflite \
  https://github.com/dscripka/openWakeWord/raw/main/openwakeword/models/hey_computer.tflite

# Test it
python train_custom_wake_word.py test custom_models/hey_computer.tflite 30

# Use it
python voice_assistant.py custom_models/hey_computer.tflite alexa 0.5 0.5 0
```

### Example 3: Train "hey companion" from scratch

```bash
# 1. Collect samples
python train_custom_wake_word.py collect "hey_companion" 30

# 2. Upload to Teachable Machine
# https://teachablemachine.withgoogle.com/train/audio
# - Upload samples as Class 1
# - Record background noise as Class 2
# - Train and export

# 3. Download and test
python train_custom_wake_word.py test custom_models/hey_companion.tflite 30

# 4. Use it
python voice_assistant.py custom_models/hey_companion.tflite alexa 0.5 0.5 0
```

---

## Resources

### OpenWakeWord
- **GitHub:** https://github.com/dscripka/openWakeWord
- **Documentation:** https://github.com/dscripka/openWakeWord/wiki
- **Pre-trained Models:** https://github.com/dscripka/openWakeWord/tree/main/openwakeword/models

### Google Teachable Machine
- **Website:** https://teachablemachine.withgoogle.com/
- **Guide:** https://teachablemachine.withgoogle.com/train/audio

### Community
- **Reddit:** r/LocalLLaMA, r/privacy
- **Discord:** OpenWakeWord community

---

## Quick Reference

| Want to... | Do this... | Time |
|------------|------------|------|
| Try different word now | `python voice_assistant.py hey_mycroft` | 1 min |
| Download ready model | Download from OpenWakeWord repo | 10 min |
| Quick custom model | Use Google Teachable Machine | 30 min |
| Professional model | Full OpenWakeWord training | 2-4 hrs |

---

## FAQ

**Q: Can I use multiple wake words?**

A: Yes! You can specify different START and STOP words:
```bash
python voice_assistant.py hey_jarvis alexa 0.5 0.5 0
# "hey jarvis" starts, "alexa" stops
```

**Q: How many training samples do I need?**

A: Minimum 20, recommended 30-50, ideal 100+ for best accuracy.

**Q: Does it work with non-English wake words?**

A: Yes! You can train models in any language. Just record samples in that language.

**Q: Can I use the same wake word for START and STOP?**

A: Not recommended - better to have distinct words to avoid confusion.

**Q: Will my custom model work on the Jetson?**

A: Yes! OpenWakeWord models are optimized for edge devices like Jetson.

---

**Ready to customize?** Start with Option 1 (try `hey_mycroft`) to see if you like a different built-in model first!
