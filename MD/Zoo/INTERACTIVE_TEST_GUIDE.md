# Interactive Zoo Listener Test Guide

Test all Zoo listeners with your own custom utterances in real-time.

---

## Quick Start

```bash
# Basic usage
python3 test_zoo_interactive.py

# Verbose mode (show DEBUG logs)
python3 test_zoo_interactive.py --verbose

# Skip GrammarGiraffe (faster, no Ollama needed)
python3 test_zoo_interactive.py --no-grammar
```

---

## Example Session

```
======================================================================
🏞️  ZOO INTERACTIVE LISTENER TEST
======================================================================

Test all Zoo listeners with your own utterances!

Available listeners:
  🦅 FillerFalcon    - Detects filler words (um, uh, like, etc.)
  🐅 TempoTiger      - Analyzes speaking rate
  🐆 LexiLynx        - Tracks vocabulary usage
  🦒 GrammarGiraffe  - Detects grammar errors (⚠️  ~500ms per utterance)

Commands:
  • Type your utterance and press Enter
  • 'quit' or 'exit' to exit
  • 'help' for this message
  • 'stats' to show vocabulary cache stats
======================================================================

📦 Initializing listeners...
  ✓ All listeners ready (including GrammarGiraffe)

Ready! Enter your first utterance below.

----------------------------------------------------------------------
💬 Enter utterance (or 'quit' to exit): What are the tools I am would using?
⏱️  Duration in seconds (press Enter to skip): 2.5
   ✓ Using 2.5s (2500ms)

📝 Utterance #1
   Text: "What are the tools I am would using?"

==================== Processing ====================

🦅 FillerFalcon analyzing...
🐅 TempoTiger analyzing...
[15:45:32] | 🐅 TempoTiger | Signal: tempo_issue 🟢 (0.22) - too_fast (192 WPM)
🐆 LexiLynx analyzing...
🦒 GrammarGiraffe analyzing (this may take ~500ms)...
[15:45:33] | 🦒 GrammarGiraffe | Signal: grammar_error 🔴 (0.85) - tense: Double auxiliary verbs

============================================================

📊 Total signals: 2

Signal breakdown:
  🟢 TempoTiger: tempo_issue (severity: 0.22)
     └─ too_fast
  🔴 GrammarGiraffe: grammar_error (severity: 0.85)
     └─ Cannot use 'am' and 'would' together

----------------------------------------------------------------------
💬 Enter utterance (or 'quit' to exit): Um, I think we should leverage our expertise
⏱️  Duration in seconds (press Enter to skip):
   ℹ️  Estimated 3.6s based on 9 words

📝 Utterance #2
   Text: "Um, I think we should leverage our expertise"

==================== Processing ====================

🦅 FillerFalcon analyzing...
[15:45:40] | 🦅 FillerFalcon | Signal: filler_detected 🟢 (0.17) - 1x (um) @ 16.7/min
🐅 TempoTiger analyzing...
🐆 LexiLynx analyzing...
[15:45:40] | 🐆 LexiLynx | Signal: vocab_used 🟢 (0.00) - leverage (verb)
🦒 GrammarGiraffe analyzing (this may take ~500ms)...

============================================================

📊 Total signals: 2

Signal breakdown:
  🟢 FillerFalcon: filler_detected (severity: 0.17)
  🟢 LexiLynx: vocab_used (severity: 0.00)

----------------------------------------------------------------------
💬 Enter utterance (or 'quit' to exit): stats

======================================================================
📊 Vocabulary Cache Statistics
======================================================================
  Words: 3
  Collocations: 2
  Total: 5

Sample vocabulary words:
  • leverage (verb)
  • facilitate (verb)
  • comprehensive (adjective)

Sample collocations:
  • take into account
  • in terms of
======================================================================

----------------------------------------------------------------------
💬 Enter utterance (or 'quit' to exit): quit

==================== Session Summary ====================

  Utterances tested: 2
  Total signals: 4
  Average signals/utterance: 2.0

Thank you for testing the Zoo listeners! 🏞️
```

---

## Test Cases to Try

### Testing GrammarGiraffe

```
Utterance: What are the tools I am would using?
Expected: tense error (double auxiliary verbs)

Utterance: I saw elephant yesterday
Expected: article error (missing "an")

Utterance: She go to store every day
Expected: subject-verb agreement error

Utterance: I have went there before
Expected: tense error (went → gone)

Utterance: The information are correct
Expected: pluralization error (information is/are)
```

### Testing FillerFalcon

```
Utterance: Um, I think, like, we should proceed
Expected: 2 fillers detected

Utterance: You know, basically, I mean, this is important
Expected: 3 fillers detected

Utterance: This is a clean sentence
Expected: No fillers
```

### Testing TempoTiger

```
Utterance: This is slow
Duration: 4 seconds
Expected: too_slow (60 WPM, threshold 100)

Utterance: This is a very fast sentence with many words
Duration: 2 seconds
Expected: too_fast (270+ WPM, threshold 180)

Utterance: Normal paced sentence here
Duration: 1.5 seconds
Expected: No issues (120-150 WPM)
```

### Testing LexiLynx

```
Utterance: We should leverage our comprehensive expertise
Expected: 2 vocab words (leverage, comprehensive)

Utterance: We need to take into account all factors
Expected: 1 collocation (take into account)

Utterance: Let me facilitate this discussion
Expected: 1 vocab word (facilitate)
```

---

## Commands

### Interactive Commands

- **quit** / **exit** / **q** - Exit the test
- **help** - Show help message
- **stats** - Show vocabulary cache statistics

### Command Line Options

```bash
# Verbose mode - show DEBUG level logs
python3 test_zoo_interactive.py --verbose

# Skip GrammarGiraffe - faster, no LLM needed
python3 test_zoo_interactive.py --no-grammar
```

---

## Duration Input

When prompted for duration:

- **Press Enter** - Auto-estimate from word count (~150 WPM)
- **Enter seconds** - Use specific duration (e.g., `2.5`, `3`, `4.2`)

Duration affects TempoTiger's WPM calculation:
- **< 100 WPM** = too slow
- **100-180 WPM** = normal
- **> 180 WPM** = too fast

---

## On Jetson (Testing GrammarGiraffe)

```bash
# Ensure Ollama is running
systemctl status ollama
# or
ollama list

# Run interactive test
cd ~/apps/english-companion-nx
python3 test_zoo_interactive.py

# Try your grammar error example:
> What are the tools I am would using?
```

Expected output:
```
🦒 GrammarGiraffe | Signal: grammar_error 🔴 (0.85) - tense: Double auxiliary verbs
```

---

## Tips

1. **Test one listener at a time**: Use specific utterances that target one listener
2. **Skip duration**: Press Enter to auto-estimate (good for quick testing)
3. **Use --no-grammar**: Skip GrammarGiraffe for faster iteration
4. **Try edge cases**: Empty strings, very long sentences, multiple issues
5. **Check vocab stats**: Use `stats` command to see what words are tracked

---

## Troubleshooting

### GrammarGiraffe Not Available

```
🦒 GrammarGiraffe  - ❌ Not available (requires Ollama)
```

**Solution:**
- Ensure Ollama is running: `ollama serve`
- Check model is loaded: `ollama list` (should show llama3.2:3b)
- Or use `--no-grammar` flag to skip

### Slow Performance

If GrammarGiraffe is slow (>1s per utterance):

```bash
# Skip it for faster testing
python3 test_zoo_interactive.py --no-grammar
```

### Import Errors

```
ModuleNotFoundError: No module named 'psutil'
```

**Solution:**
- Run in virtual environment: `source .venv/bin/activate`
- Or install dependencies: `pip install -r requirements-jetson.txt`

---

## Sample Test Scenarios

### Scenario 1: Filler Detection

```
Utterance: Um, like, I think we should, you know, proceed
Duration: [Enter]
Expected:
  🦅 FillerFalcon: 4 fillers detected
  Severity: High (40-50/min rate)
```

### Scenario 2: Grammar + Vocab

```
Utterance: I saw elephant but we should leverage this opportunity
Duration: 3
Expected:
  🦒 GrammarGiraffe: article error (elephant → an elephant)
  🐆 LexiLynx: vocab_used (leverage)
```

### Scenario 3: Clean Utterance

```
Utterance: This is a perfectly clean sentence
Duration: 2
Expected:
  ✅ No issues detected - clean utterance!
```

### Scenario 4: Everything at Once

```
Utterance: Um, I saw elephant and we should leverage comprehensive solution
Duration: 5
Expected:
  🦅 FillerFalcon: filler_detected (um)
  🦒 GrammarGiraffe: grammar_error (elephant)
  🐆 LexiLynx: vocab_used (leverage, comprehensive)
  Multiple signals!
```

---

## Exit and Summary

Press Ctrl+C or type `quit` to exit:

```
==================== Session Summary ====================

  Utterances tested: 5
  Total signals: 12
  Average signals/utterance: 2.4

Thank you for testing the Zoo listeners! 🏞️
```

---

## Integration with Voice Assistant

This interactive test uses the same listener code as the voice assistant.
Results here will match what you'd see in real conversations!

To integrate logging into voice assistant:
```python
from src.zoo.zoo_logger import get_zoo_logger

logger = get_zoo_logger()
# Listeners will automatically log to console
```

---

## See Also

- `demo_zoo_listeners.py` - Automated demo with pre-defined utterances
- `ZOO_LOGGING_GUIDE.md` - Complete logging system reference
- `LISTENER_USAGE_GUIDE.md` - Listener API documentation
