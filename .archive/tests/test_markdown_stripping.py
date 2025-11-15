#!/usr/bin/env python3
"""
Test script for markdown stripping in TTS
"""

import re


def strip_markdown(text: str) -> str:
    """
    Strip markdown formatting from text for TTS
    (Copied from src/speech/synthesis.py for standalone testing)
    """
    # Remove code blocks first (multiline)
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)

    # Remove inline code
    text = re.sub(r'`([^`]+)`', r'\1', text)

    # Remove links but keep link text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

    # Remove bold/italic (order matters - do bold first)
    text = re.sub(r'\*\*\*([^\*]+)\*\*\*', r'\1', text)  # Bold+italic
    text = re.sub(r'___([^_]+)___', r'\1', text)
    text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)  # Bold
    text = re.sub(r'__([^_]+)__', r'\1', text)
    text = re.sub(r'\*([^\*]+)\*', r'\1', text)  # Italic
    text = re.sub(r'_([^_]+)_', r'\1', text)

    # Remove strikethrough
    text = re.sub(r'~~([^~]+)~~', r'\1', text)

    # Remove headers (# ## ###)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

    # Remove bullet points at start of lines
    text = re.sub(r'^\s*[\*\-\+]\s+', '', text, flags=re.MULTILINE)

    # Remove numbered lists at start of lines
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)

    # Clean up extra whitespace
    text = re.sub(r'\n\s+', '\n', text)  # Remove leading spaces after newlines
    text = re.sub(r'\n{3,}', '\n\n', text)  # Max 2 newlines in a row
    text = text.strip()

    return text


def test_markdown_stripping():
    """Test various markdown patterns"""

    test_cases = [
        # Bold
        ("I like reading books **that** interest me.",
         "I like reading books that interest me."),

        # Bullet points
        ("* I like reading books\n* I enjoy hiking\n* I love coffee",
         "I like reading books\nI enjoy hiking\nI love coffee"),

        # Italic
        ("This is *very* important.",
         "This is very important."),

        # Combined
        ("* I like reading books **that** interest me\n* She *always* helps others",
         "I like reading books that interest me\nShe always helps others"),

        # Headers (double newlines collapsed to single for TTS)
        ("# My Interests\n\nI like reading.",
         "My Interests\nI like reading."),

        # Links
        ("Check out [this article](https://example.com) for more info.",
         "Check out this article for more info."),

        # Code
        ("Use the `print()` function to display text.",
         "Use the print() function to display text."),

        # Numbered lists
        ("1. First item\n2. Second item\n3. Third item",
         "First item\nSecond item\nThird item"),
    ]

    print("🧪 Testing Markdown Stripping for TTS\n")
    print("=" * 70)

    all_passed = True

    for i, (input_text, expected) in enumerate(test_cases, 1):
        result = strip_markdown(input_text)
        passed = result.strip() == expected.strip()

        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"\nTest {i}: {status}")
        print(f"Input:    {repr(input_text)}")
        print(f"Expected: {repr(expected)}")
        print(f"Got:      {repr(result)}")

        if not passed:
            all_passed = False

    print("\n" + "=" * 70)

    if all_passed:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")

    return all_passed


if __name__ == "__main__":
    success = test_markdown_stripping()
    exit(0 if success else 1)
