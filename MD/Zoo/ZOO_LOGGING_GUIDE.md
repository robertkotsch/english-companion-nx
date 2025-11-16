# Zoo Logging System Guide

Visual logging system for Zoo agent activity during conversations.

---

## Overview

The Zoo logging system provides clear, visual feedback about what each agent is doing during conversation processing. Each agent has a distinctive emoji marker for easy identification.

### Agent Markers

**Listeners (Phase 1.2):**
- 🦅 **FillerFalcon** - Filler word detection
- 🐅 **TempoTiger** - Speaking tempo analysis
- 🦒 **GrammarGiraffe** - Grammar error detection
- 🐆 **LexiLynx** - Vocabulary usage tracking

**Orchestrator (Phase 1.4):**
- 🐙 **OrchestratorOctopus** - Signal processing and decisions

**Memory (Phase 1.3):**
- 🐦 **NotionNightingale** - Notion vocabulary sync
- 🐿️  **SpacedSquirrel** - Spaced repetition scheduling
- 🐼 **PersonaPanda** - User profile management

**Coaching (Phase 1.5):**
- 🐺 **CoachCoyote** - Main conversational coach
- 🐯 **TaskTiger** - Drill designer
- 🦜 **FocusFalcon** - Focus area selector
- 🐑 **SessionShepherd** - Session planning

**Flow (Phase 1.6):**
- 🐬 **DayDolphin** - Day state machine
- 🐦‍⬛ **ScribeSparrow** - Session logging
- 🦬 **BoundaryBison** - Intensity management

---

## Quick Start

### Using the Demo

```bash
# Basic demo - shows all listeners in action
python3 demo_zoo_listeners.py

# Verbose mode - shows DEBUG level logs
python3 demo_zoo_listeners.py --verbose

# Test grammar listener (requires Ollama)
python3 demo_zoo_listeners.py --test-grammar
```

### Sample Output

```
==================== Utterance #1: Fillers + Vocab ====================

  💬 Text: "Um, I think we should leverage our expertise"
  ⏱️  Duration: 3500ms

[15:17:47] | 🦅 FillerFalcon | Signal: filler_detected 🔴 (1.00) - 2x (um, like) @ 34.3/min
[15:17:47] | 🐆 LexiLynx | Signal: vocab_used 🟢 (0.00) - leverage (verb)

  📊 Total signals: 2
```

---

## Using in Code

### Basic Setup

```python
from src.zoo.zoo_logger import get_zoo_logger

# Get global logger instance
logger = get_zoo_logger()

# Use in listener
class MyListener(BaseListener):
    def __init__(self):
        super().__init__()
        self.logger = get_zoo_logger()

    def process_utterance(self, text, metadata):
        # Log signal emission
        self.logger.listener_signal(
            self.name,
            signal_type="my_signal",
            severity=0.6,
            details="Found 3 issues"
        )

        # Log no issues
        self.logger.listener_no_signal(self.name)
```

### Log Levels

```python
from src.zoo.zoo_logger import set_zoo_log_level
import logging

# Show everything (DEBUG)
set_zoo_log_level(logging.DEBUG)

# Normal operation (INFO) - default
set_zoo_log_level(logging.INFO)

# Errors only
set_zoo_log_level(logging.ERROR)
```

### Signal Logging

```python
# Signal emitted
logger.listener_signal(
    agent_name="FillerFalcon",
    signal_type="filler_detected",
    severity=0.8,  # 0.0-1.0
    details="3x fillers @ 45/min"
)

# No issues found
logger.listener_no_signal("FillerFalcon")

# Processing error
logger.listener_error("FillerFalcon", "Failed to parse text")
```

### Severity Color Coding

Signals are automatically color-coded by severity:
- 🔴 **High** (severity > 0.7) - Critical issues
- 🟡 **Medium** (0.4-0.7) - Moderate issues
- 🟢 **Low** (< 0.4) - Minor issues or informational

---

## Orchestrator Logging (Phase 1.4)

```python
# Decision logging
logger.orchestrator_decision(
    action="DRILL_NOW",
    signal_count=3,
    details="High-severity grammar error"
)
```

---

## Memory Agent Logging (Phase 1.3)

```python
# Memory updates
logger.memory_update(
    agent_name="NotionNightingale",
    update_type="sync_complete",
    details="45 words synced"
)
```

---

## Coach Logging (Phase 1.5)

```python
# Coach responses
logger.coach_response(
    agent_name="CoachCoyote",
    response_type="drill_delivery",
    details="Filler reduction exercise"
)
```

---

## Session Events (Phase 1.6)

```python
# Session events
logger.session_event(
    event_type="session_start",
    details="Quick session (7 min target)"
)

# Phase transitions
logger.phase_transition(
    from_phase="WAITING_FOR_USER",
    to_phase="IN_SESSION"
)
```

---

## Visual Elements

### Separators

```python
# Simple separator
logger.separator()
# ============================================================

# Separator with title
logger.separator("Processing Utterance #5")
# ==================== Processing Utterance #5 ====================
```

### Summaries

```python
logger.summary(
    title="Session Results",
    items=[
        "Duration: 12.5 minutes",
        "Utterances: 24",
        "Drills completed: 3/5",
        "Vocab used: leverage, facilitate, comprehensive"
    ]
)
```

Output:
```
==================== Session Results ====================
  • Duration: 12.5 minutes
  • Utterances: 24
  • Drills completed: 3/5
  • Vocab used: leverage, facilitate, comprehensive
============================================================
```

---

## Generic Logging

For cases not covered by specialized methods:

```python
# Info level
logger.info("MyAgent", "Processing started")

# Debug level
logger.debug("MyAgent", "Intermediate step complete")

# Warning level
logger.warning("MyAgent", "Threshold nearly exceeded")

# Error level
logger.error("MyAgent", "Failed to complete task")
```

---

## Configuration Options

```python
from src.zoo.zoo_logger import ZooLogger

# Create custom logger instance
logger = ZooLogger(
    name="CustomZoo",
    level=logging.INFO,
    show_timestamps=True,  # Show [HH:MM:SS] timestamps
    colorize=True          # Use ANSI color codes
)
```

### Disable Timestamps

```python
logger = ZooLogger(show_timestamps=False)
```

Output:
```
🦅 FillerFalcon | Signal: filler_detected 🔴 (1.00) - 2x @ 34.3/min
```

### Disable Colors (for file logging)

```python
logger = ZooLogger(colorize=False)
```

---

## Integration with Phase 2B Voice Assistant

To add Zoo logging to existing voice assistant:

```python
# In voice_assistant.py
from src.zoo.zoo_logger import get_zoo_logger, set_zoo_log_level
import logging

# Set up logging at startup
set_zoo_log_level(logging.INFO)  # or DEBUG for verbose
logger = get_zoo_logger()

# Show session start
logger.separator("Voice Assistant Starting")

# In conversation loop
logger.separator(f"Utterance #{utterance_count}")

# After processing listeners
if signals:
    logger.info("Zoo", f"Received {len(signals)} signals")
```

---

## Demo Utterances

The demo includes 7 test utterances demonstrating different listener behaviors:

1. **Fillers + Vocab** - Mixed issues
2. **Too Fast** - 330 WPM (threshold: 180)
3. **Too Slow** - 45 WPM (threshold: 100)
4. **Vocab + Collocation** - Target words used correctly
5. **Multiple Fillers** - 5 different filler types
6. **Baseline** - Clean utterance (expected no issues)
7. **Multiple Vocab** - 3 target words in one utterance

---

## Troubleshooting

### No Color Output

If you don't see colors in terminal:
- Check terminal supports ANSI colors
- Try `colorize=False` for plain text

### Logs Not Appearing

```python
# Ensure log level is not too restrictive
set_zoo_log_level(logging.DEBUG)

# Check logger is initialized
logger = get_zoo_logger()
```

### Timestamps Wrong Timezone

Timestamps use system local time. To change:
```python
# Edit zoo_logger.py, line with strftime()
timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
```

---

## Performance

Logging overhead is minimal:
- Console output: ~0.1ms per log line
- String formatting: ~0.05ms per message
- **Total impact:** <1ms per utterance

Safe to use in real-time conversation loops.

---

## Future Enhancements (Post-MVP)

- **File logging** - Log to rotating files for analysis
- **Dashboard integration** - Real-time web dashboard
- **Statistics** - Aggregated signal counts, timing
- **Filtering** - Show/hide specific agent types
- **Replay mode** - Replay logged sessions

---

## Example: Full Conversation Flow

```python
logger = get_zoo_logger()

# Session start
logger.session_event("session_start", "Full session (20 min)")

# User utterance
logger.separator("Utterance #1")
print("💬 User: Um, I think we should leverage this")

# Listeners process
# (FillerFalcon logs automatically)
# (LexiLynx logs automatically)

# Orchestrator decides
logger.orchestrator_decision("DRILL_NOW", signal_count=2, details="Filler drill")

# Coach responds
logger.coach_response("CoachCoyote", "drill_delivery", "Repeat without 'um'")

# Session summary
logger.summary("Session Complete", [
    "Duration: 18.5 min",
    "Drills: 4 completed",
    "Progress: +2 vocab mastery"
])
```

---

## See Also

- `demo_zoo_listeners.py` - Live demo script
- `PHASE_1.2_SUMMARY.md` - Implementation details
- `LISTENER_USAGE_GUIDE.md` - Listener API reference
