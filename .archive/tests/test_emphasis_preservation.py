#!/usr/bin/env python3
"""
Test script for markdown emphasis preservation in TTS
Tests the convert_markdown_emphasis_to_pauses function
"""

import re


def convert_markdown_emphasis_to_pauses(text: str) -> str:
    """
    Convert markdown emphasis (bold/italic) to natural pauses for TTS
    (Copied from src/speech/synthesis.py for standalone testing)
    """
    # Convert bold+italic to emphasized word with pause
    text = re.sub(r'\*\*\*([^\*]+)\*\*\*', r', \1,', text)
    text = re.sub(r'___([^_]+)___', r', \1,', text)

    # Convert bold to word with slight pause (comma before)
    text = re.sub(r'\*\*([^\*]+)\*\*', r', \1', text)
    text = re.sub(r'__([^_]+)__', r', \1', text)

    # Remove italic markers (keep word unchanged)
    text = re.sub(r'\*([^\*]+)\*', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)

    # Clean up double commas and spaces
    text = re.sub(r',\s*,', ',', text)
    text = re.sub(r'\s+,', ',', text)
    text = re.sub(r',\s+', ', ', text)

    return text


def test_emphasis_preservation():
    """Test emphasis preservation with various patterns"""

    test_cases = [
        # Basic bold emphasis
        ("I like reading books **that** interest me.",
         "I like reading books, that interest me.",
         "Bold word gets pause before it"),

        # Multiple bold words
        ("This is **very** **important** information.",
         "This is, very, important information.",
         "Multiple bold words each get pauses"),

        # Bold phrase
        ("I like reading books **that interest me** today.",
         "I like reading books, that interest me today.",
         "Bold phrase gets pause before it"),

        # Italic (should be removed without emphasis)
        ("This is *very* important.",
         "This is very important.",
         "Italic markers removed, no pause added"),

        # Bold + italic combined
        ("This is ***extremely*** important.",
         "This is, extremely, important.",
         "Bold+italic gets pause before AND after"),

        # Mixed bold and italic
        ("**Important**: Please *note* this **carefully**.",
         ", Important: Please note this, carefully.",
         "Bold gets pauses, italic removed"),

        # Emphasis at start of sentence
        ("**Listen**: this is critical.",
         ", Listen: this is critical.",
         "Bold at start gets leading comma"),

        # Real-world example from LLM (bullets treated as italic, stripped)
        ("* I like reading books **that** interest me\n* She *always* helps others",
         " I like reading books, that interest me\n She always helps others",
         "Emphasis preserved, bullets treated as italic"),
    ]

    print("🧪 Testing Emphasis Preservation for TTS\n")
    print("=" * 70)

    all_passed = True

    for i, (input_text, expected, description) in enumerate(test_cases, 1):
        result = convert_markdown_emphasis_to_pauses(input_text)
        passed = result == expected

        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"\nTest {i}: {status} - {description}")
        print(f"Input:    {repr(input_text)}")
        print(f"Expected: {repr(expected)}")
        print(f"Got:      {repr(result)}")

        if not passed:
            all_passed = False
            # Show diff
            print(f"Diff:     Expected '{expected}'")
            print(f"          Got      '{result}'")

    print("\n" + "=" * 70)

    # Examples of how it sounds
    print("\n📢 How This Sounds in TTS:\n")
    print("Without emphasis preservation:")
    print('  "I like reading books that interest me"')
    print("  (flat, no emphasis)\n")

    print("With emphasis preservation:")
    print('  "I like reading books, that interest me"')
    print("  (slight pause before 'that' creates natural emphasis)\n")

    print("=" * 70)

    if all_passed:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")

    return all_passed


if __name__ == "__main__":
    success = test_emphasis_preservation()
    exit(0 if success else 1)
