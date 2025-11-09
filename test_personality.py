#!/usr/bin/env python3
"""
Test personality profile loading
Shows which personality is loaded and its content
"""

from src.core.config import Config
from src.conversation.manager import ConversationManager


def main():
    print("=" * 70)
    print("🎭 English Companion NX - Personality Profile Test")
    print("=" * 70)

    # Show configured personality
    print(f"\n📋 Configured personality: {Config.PERSONALITY_PROFILE}")

    # Initialize conversation manager (loads personality)
    print("\n📦 Loading personality profile...")
    manager = ConversationManager()

    # Get the loaded system prompt from history
    system_prompt = manager.history[0]["content"]

    # Display the personality
    print("\n" + "=" * 70)
    print("🎭 Loaded Personality Profile:")
    print("=" * 70)
    print(system_prompt)
    print("=" * 70)

    # Show available personalities
    from pathlib import Path
    personalities_dir = Path(__file__).parent / "personalities"
    available = sorted([f.stem for f in personalities_dir.glob("*.txt")])

    print(f"\n📚 Available personalities:")
    for personality in available:
        indicator = "✓" if personality == Config.PERSONALITY_PROFILE else " "
        print(f"  [{indicator}] {personality}")

    print("\n💡 To change personality, edit PERSONALITY_PROFILE in your .env file")
    print("=" * 70)


if __name__ == "__main__":
    main()
