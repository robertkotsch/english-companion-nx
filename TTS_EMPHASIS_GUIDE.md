# TTS Emphasis Guide - English Companion NX

## Overview

Since Coqui VITS (`tts_models/en/ljspeech/vits`) doesn't support SSML or prosody control, we simulate emphasis through **natural pauses** created by commas.

## How It Works

### Problem
LLMs often use markdown **bold** to emphasize words:
```
"I like reading books **that** interest me."
```

Without emphasis handling, TTS speaks this flatly with no emphasis.

### Solution
Convert bold markdown to pauses (commas):
```
Input:  "I like reading books **that** interest me."
Output: "I like reading books, that interest me."
TTS:    "I like reading books [pause] that interest me."
```

The pause before "that" creates natural emphasis!

## Configuration

### Enable/Disable

**Enabled by default** - Add to `.env`:
```bash
TTS_PRESERVE_EMPHASIS=true   # Convert **word** to pauses (default)
TTS_PRESERVE_EMPHASIS=false  # Strip **word** to plain text
```

### What Gets Converted

| Markdown | Output | Effect |
|----------|--------|--------|
| `**word**` | `, word` | Slight pause before word |
| `***word***` | `, word,` | Pause before AND after |
| `*word*` | `word` | Italic removed, no pause |
| `ALL CAPS` | `ALL CAPS` | Kept as-is (TTS naturally emphasizes) |

## Examples

### Example 1: Single Word Emphasis
```
LLM:  "This is **very** important."
TTS:  "This is, very important."
Says: "This is [pause] very important."
```

### Example 2: Multiple Emphasis
```
LLM:  "Please **listen** **carefully**."
TTS:  "Please, listen, carefully."
Says: "Please [pause] listen [pause] carefully."
```

### Example 3: Strong Emphasis
```
LLM:  "This is ***critical***!"
TTS:  "This is, critical,!"
Says: "This is [pause] critical [pause]!"
```

### Example 4: Phrase Emphasis
```
LLM:  "I like reading books **that interest me**."
TTS:  "I like reading books, that interest me."
Says: "I like reading books [pause] that interest me."
```

## Prompt Engineering for Better Emphasis

Instead of relying on markdown, you can train the LLM to use natural emphasis:

```python
system_prompt = """...
When emphasizing words, use these techniques:
- Use stronger vocabulary instead of bold (e.g., "crucial" instead of "**important**")
- Add ellipses for dramatic pauses: "Listen carefully... this is important."
- Use ALL CAPS sparingly for strong emphasis
- Vary sentence structure to create natural rhythm
"""
```

## Testing

```bash
# Test emphasis preservation
python test_emphasis_preservation.py

# Expected: All 8 tests pass
```

## Limitations

### What VITS Cannot Do

❌ **Pitch control** - Cannot make words higher/lower pitch
❌ **Rate control** - Cannot speed up/slow down specific words
❌ **Volume control** - Cannot make words louder/quieter
❌ **SSML tags** - No `<emphasis>`, `<prosody>`, or `<phoneme>` support
❌ **Emotion parameters** - `emotion` parameter doesn't work with VITS

### What Works

✅ **Pause-based emphasis** - Using commas for natural pauses
✅ **ALL CAPS** - TTS naturally emphasizes capitalized text
✅ **Punctuation** - Ellipses (...) create longer pauses
✅ **Word choice** - Strong vocabulary creates natural emphasis

## Alternative: Upgrade to XTTS-v2

For better prosody control, consider upgrading:

**XTTS-v2 Features:**
- ✅ More natural emotion/intonation
- ✅ Voice cloning from reference audio
- ✅ Better emphasis through conditioning

**Tradeoffs:**
- ❌ Slower (~10-15s vs ~2.5s per response)
- ❌ More VRAM (~4-6GB vs ~1GB)
- ❌ Still no SSML support

**Not recommended for Jetson 24/7 deployment** - Current VITS model is more reliable.

## Technical Details

**Location:** `src/speech/synthesis.py`

**Functions:**
- `convert_markdown_emphasis_to_pauses()` - Converts bold to pauses
- `strip_markdown()` - Removes all markdown (calls emphasis converter if enabled)

**Processing Flow:**
1. LLM generates response with markdown
2. `strip_markdown(text, preserve_emphasis=True)` called
3. If `TTS_PRESERVE_EMPHASIS=true`, bold → commas
4. Other markdown (bullets, links, etc.) stripped
5. Clean text sent to TTS

## Troubleshooting

### Too Many Pauses

If speech sounds choppy, disable emphasis preservation:
```bash
TTS_PRESERVE_EMPHASIS=false
```

### Not Enough Emphasis

If words need more emphasis:
1. Use prompt engineering (stronger vocabulary)
2. Ask LLM to use ALL CAPS for critical words
3. Use ellipses for dramatic pauses

### Leading Comma at Start

Bold at sentence start creates leading comma:
```
Input:  "**Listen**: this is important."
Output: ", Listen: this is important."
```

This is intentional - creates natural emphasis. If unwanted, disable feature.

## Summary

| Feature | Status |
|---------|--------|
| Markdown stripping | ✅ Automatic |
| Emphasis preservation | ✅ Configurable (default: ON) |
| SSML support | ❌ Not available |
| Prosody control | ❌ Not available |
| Pause-based emphasis | ✅ Working |

**Recommendation:** Keep `TTS_PRESERVE_EMPHASIS=true` for natural-sounding emphasis without LLM prompt changes.

---

**Last Updated:** January 2025
**Model:** `tts_models/en/ljspeech/vits`
**Test Status:** All 8 tests passing ✅
