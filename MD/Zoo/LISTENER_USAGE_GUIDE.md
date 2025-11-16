# Zoo Listeners - Quick Usage Guide

Quick reference for using the Phase 1.2 listener agents.

---

## Basic Usage

### Importing Listeners

```python
from src.zoo.listeners import (
    FillerFalcon,
    TempoTiger,
    GrammarGiraffe,
    LexiLynx,
)
```

### Simple Example

```python
# Create listener instances
filler_listener = FillerFalcon()
tempo_listener = TempoTiger()
grammar_listener = GrammarGiraffe()
vocab_listener = LexiLynx()

# User utterance
text = "Um, I think we should leverage our expertise here"
metadata = {
    'utterance_id': 'abc-123',
    'timestamp': 1234567890.0,
    'duration_ms': 3500,
}

# Process with each listener
filler_signals = filler_listener.process_utterance(text, metadata)
tempo_signals = tempo_listener.process_utterance(text, metadata)
grammar_signals = grammar_listener.process_utterance(text, metadata)
vocab_signals = vocab_listener.process_utterance(text, metadata)

# Combine all signals
all_signals = filler_signals + tempo_signals + grammar_signals + vocab_signals

# Process signals (orchestrator will do this in Phase 1.4)
for signal in all_signals:
    print(f"{signal.source}: {signal.type} (severity: {signal.severity})")
    print(f"  Data: {signal.data}")
```

---

## Listener Details

### FillerFalcon

**Detects:** um, uh, like, you know, basically, actually, I mean, kind of, sort of, etc.

```python
# Default configuration
listener = FillerFalcon()

# Custom configuration
config = {
    'threshold_per_min': 5.0,  # Max fillers/min before signaling
    'min_count_for_signal': 2,  # Need 2+ fillers to emit signal
}
listener = FillerFalcon(config)

# Process
signals = listener.process_utterance("Um, this is, like, important")

# Signal data
# {
#   'filler': 'um',
#   'position': 0,
#   'count': 2,
#   'rate_per_min': 40.0,
#   'all_fillers': [{'word': 'um', 'position': 0}, ...]
# }
```

---

### TempoTiger

**Detects:** Too slow (<100 WPM), too fast (>180 WPM), long pauses (>2s)

```python
# Default configuration
listener = TempoTiger()

# Custom configuration
config = {
    'min_wpm': 120,  # Slower than 120 WPM is flagged
    'max_wpm': 160,  # Faster than 160 WPM is flagged
    'long_pause_threshold_sec': 1.5,  # Pauses >1.5s flagged
}
listener = TempoTiger(config)

# Process with duration only
metadata = {'duration_ms': 4000}  # 4 seconds
signals = listener.process_utterance("This is a test", metadata)

# Process with word timestamps (more detailed)
metadata = {
    'duration_ms': 5000,
    'word_timestamps': [
        {'word': 'Hello', 'start': 0.0, 'end': 0.5},
        {'word': 'world', 'start': 0.7, 'end': 1.2},
        {'word': 'how', 'start': 3.5, 'end': 3.8},  # Long pause before
    ]
}
signals = listener.process_utterance("Hello world how", metadata)

# Signal data (WPM issue)
# {
#   'issue_type': 'too_slow',
#   'wpm': 60.0,
#   'target_wpm': 100
# }

# Signal data (Pause issue)
# {
#   'issue_type': 'long_pause',
#   'pause_duration_sec': 2.3,
#   'pause_after_word': 'world',
#   'pause_position': 1
# }
```

---

### GrammarGiraffe

**Detects:** Articles, tense, word order, subject-verb, prepositions, pluralization, pronouns

**Note:** Requires Ollama to be running (llama3.2:3b)

```python
# Default configuration
listener = GrammarGiraffe()

# Custom configuration
config = {
    'min_severity': 0.5,  # Only emit signals for moderate+ errors
    'llm_temperature': 0.1,  # More deterministic analysis
    'categories': ['articles', 'tense'],  # Only check specific categories
}
listener = GrammarGiraffe(config)

# Process
signals = listener.process_utterance("I saw elephant yesterday")

# Signal data
# {
#   'error_type': 'articles',
#   'original': 'I saw elephant',
#   'suggestion': 'I saw an elephant',
#   'explanation': 'Missing article before vowel sound'
# }
```

**Performance Note:** ~500ms per utterance due to LLM call. Run in background thread if needed.

---

### LexiLynx

**Detects:** Target vocabulary words and collocations from cache

```python
# Default configuration (uses data/vocab/cache.json)
listener = LexiLynx()

# Custom cache path
config = {
    'vocab_cache_path': 'my_custom_vocab.json',
    'check_collocations': True,
}
listener = LexiLynx(config)

# Process
signals = listener.process_utterance("We should leverage this opportunity")

# Signal data
# {
#   'word': 'leverage',
#   'correct': True,
#   'word_type': 'verb',
#   'definition': 'use strategically to maximum advantage'
# }

# Reload cache after update (e.g., after NotionNightingale sync)
listener.reload_cache()

# Get cache statistics
stats = listener.get_vocab_stats()
# {'words': 3, 'collocations': 2, 'total': 5}
```

---

## Parallel Processing (Recommended)

All listeners are independent - run them in parallel for best performance:

```python
import concurrent.futures

def process_with_listeners(text, metadata):
    listeners = [
        FillerFalcon(),
        TempoTiger(),
        GrammarGiraffe(),  # Slowest (~500ms)
        LexiLynx(),
    ]

    # Process in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(listener.process_utterance, text, metadata)
            for listener in listeners
        ]

        # Collect all signals
        all_signals = []
        for future in concurrent.futures.as_completed(futures):
            signals = future.result()
            all_signals.extend(signals)

    return all_signals

# Total time: ~500ms (GrammarGiraffe dominates)
# vs ~660ms serial
```

---

## Error Handling

All listeners raise `ListenerProcessingError` on failure:

```python
from src.zoo.listeners.base import ListenerProcessingError

try:
    signals = listener.process_utterance(text, metadata)
except ListenerProcessingError as e:
    print(f"Listener failed: {e}")
    # Log error, continue with other listeners
```

---

## Signal Structure

All signals follow the same structure:

```python
signal = Signal(
    source="FillerFalcon",           # Listener name
    type="filler_detected",          # Signal type constant
    severity=0.6,                    # 0.0-1.0 (0=info, 1=critical)
    scope="utterance",               # "utterance" | "session" | "trend"
    realtime_desirable=True,         # Should trigger immediate action?
    data={...},                      # Listener-specific payload
    timestamp=1234567890.0,          # Unix timestamp
    utterance_id="abc-123",          # Links to utterance
)

# Convert to dict for logging/serialization
signal_dict = signal.to_dict()

# Restore from dict
signal_restored = Signal.from_dict(signal_dict)
```

---

## Integration with Phase 2B Voice Assistant

To add listeners to existing voice assistant:

```python
# In voice_assistant.py, after Whisper transcription:

from src.zoo.listeners import FillerFalcon, TempoTiger, LexiLynx

# Initialize listeners once at startup
filler_listener = FillerFalcon()
tempo_listener = TempoTiger()
vocab_listener = LexiLynx()

# In conversation loop, after user_text is transcribed:
metadata = {
    'utterance_id': f"session-{session_id}-{utterance_count}",
    'timestamp': time.time(),
    'duration_ms': int(recording_duration * 1000),
}

# Process in parallel
signals = []
signals.extend(filler_listener.process_utterance(user_text, metadata))
signals.extend(tempo_listener.process_utterance(user_text, metadata))
signals.extend(vocab_listener.process_utterance(user_text, metadata))

# For now, just log signals (Phase 1.4 will add Orchestrator)
for signal in signals:
    logger.info(f"Signal: {signal.source} - {signal.type} (severity: {signal.severity})")

# Continue with normal LLM flow...
```

---

## Testing

Run tests to verify listeners work:

```bash
# Simple standalone tests (no venv needed)
python3 test_zoo_listeners_simple.py

# Full unittest suite (requires venv)
source ~/apps/english-companion-nx/.venv/bin/activate
python test_zoo_listeners.py
```

---

## Configuration via Environment

Planned for Phase 1.7 integration:

```bash
# In .env file
ZOO_FILLER_THRESHOLD=3.0
ZOO_TEMPO_MIN_WPM=100
ZOO_TEMPO_MAX_WPM=180
ZOO_GRAMMAR_MIN_SEVERITY=0.5
ZOO_VOCAB_CACHE_PATH=data/vocab/cache.json
```

---

## Performance Monitoring

Track listener performance:

```python
import time

start = time.time()
signals = listener.process_utterance(text, metadata)
duration = time.time() - start

print(f"{listener.name}: {len(signals)} signals in {duration*1000:.1f}ms")
```

Expected performance:
- FillerFalcon: <10ms
- TempoTiger: ~50ms
- GrammarGiraffe: ~500ms (LLM)
- LexiLynx: ~100ms

---

## Next Steps

- **Phase 1.3:** Memory agents (NotionNightingale will populate vocab cache)
- **Phase 1.4:** OrchestratorOctopus (will consume and prioritize signals)
- **Phase 1.5:** Coaching agents (will act on signals with drills)

For now, listeners can run independently and log signals for observation.
