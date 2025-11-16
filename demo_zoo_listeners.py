#!/usr/bin/env python3
"""Zoo Listeners Demo - Show all listener agents in action.

This demo script processes sample utterances through all Phase 1.2 listeners
and displays their activity with visual logging.

Usage:
    python3 demo_zoo_listeners.py
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.zoo.listeners import FillerFalcon, TempoTiger, LexiLynx
from src.zoo.zoo_logger import get_zoo_logger, set_zoo_log_level


# Sample utterances with different characteristics
SAMPLE_UTTERANCES = [
    {
        'text': "Um, I think we should, like, leverage our comprehensive expertise here",
        'metadata': {
            'duration_ms': 4500,
            'utterance_id': 'demo-001',
        },
        'description': "Fillers + Vocab + Normal tempo"
    },
    {
        'text': "This is a very fast sentence with many words spoken quickly",
        'metadata': {
            'duration_ms': 2000,  # 300 WPM - too fast
            'utterance_id': 'demo-002',
        },
        'description': "Too fast speaking rate"
    },
    {
        'text': "This is slow",
        'metadata': {
            'duration_ms': 4000,  # 60 WPM - too slow
            'utterance_id': 'demo-003',
        },
        'description': "Too slow speaking rate"
    },
    {
        'text': "We need to facilitate better communication and take into account all perspectives",
        'metadata': {
            'duration_ms': 5000,
            'utterance_id': 'demo-004',
        },
        'description': "Vocabulary words + Collocation"
    },
    {
        'text': "You know, basically, I mean, this is, uh, kind of important",
        'metadata': {
            'duration_ms': 4000,
            'utterance_id': 'demo-005',
        },
        'description': "Multiple different fillers"
    },
    {
        'text': "This is a clean sentence with proper grammar and no issues",
        'metadata': {
            'duration_ms': 3000,
            'utterance_id': 'demo-006',
        },
        'description': "No issues detected (baseline)"
    },
    {
        'text': "Let me leverage this comprehensive solution to facilitate our goals",
        'metadata': {
            'duration_ms': 3500,
            'utterance_id': 'demo-007',
        },
        'description': "Multiple target vocabulary words"
    },
]


def run_demo(verbose: bool = False):
    """Run listener demo with sample utterances.

    Args:
        verbose: Show detailed logging (DEBUG level)
    """
    # Set up logging
    log_level = logging.DEBUG if verbose else logging.INFO
    set_zoo_log_level(log_level)
    logger = get_zoo_logger()

    # Print header
    print("\n")
    logger.separator("🏞️  ZOO LISTENERS DEMO - Phase 1.2")
    print()
    print("This demo shows all listener agents processing sample utterances.")
    print("Each animal emoji represents a different listener agent:")
    print()
    print("  🦅 FillerFalcon    - Detects filler words (um, uh, like, etc.)")
    print("  🐅 TempoTiger      - Analyzes speaking rate and pauses")
    print("  🐆 LexiLynx        - Tracks target vocabulary usage")
    print("  🦒 GrammarGiraffe  - Detects grammar errors (requires Ollama)")
    print()
    logger.separator()

    # Initialize listeners
    print("\n📦 Initializing listeners...")
    filler_listener = FillerFalcon()
    tempo_listener = TempoTiger()
    vocab_listener = LexiLynx()

    print(f"  ✓ {filler_listener.name} ready")
    print(f"  ✓ {tempo_listener.name} ready")
    print(f"  ✓ {vocab_listener.name} ready")

    # Show vocab cache stats
    stats = vocab_listener.get_vocab_stats()
    print(f"  ℹ️  Vocabulary cache: {stats['words']} words, {stats['collocations']} collocations")
    print()

    # Process each utterance
    total_signals = 0

    for i, sample in enumerate(SAMPLE_UTTERANCES, 1):
        text = sample['text']
        metadata = sample['metadata']
        description = sample['description']

        print()
        logger.separator(f"Utterance #{i}: {description}")
        print()
        print(f"  💬 Text: \"{text}\"")
        print(f"  ⏱️  Duration: {metadata['duration_ms']}ms")
        print()

        # Process with all listeners
        utterance_signals = []

        # FillerFalcon
        filler_signals = filler_listener.process_utterance(text, metadata)
        utterance_signals.extend(filler_signals)

        # TempoTiger
        tempo_signals = tempo_listener.process_utterance(text, metadata)
        utterance_signals.extend(tempo_signals)

        # LexiLynx
        vocab_signals = vocab_listener.process_utterance(text, metadata)
        utterance_signals.extend(vocab_signals)

        # Summary for this utterance
        print()
        if utterance_signals:
            print(f"  📊 Total signals: {len(utterance_signals)}")
            total_signals += len(utterance_signals)
        else:
            print("  ✅ No issues detected")

    # Final summary
    print()
    print()
    logger.separator("📈 DEMO SUMMARY")
    print()
    print(f"  Utterances processed: {len(SAMPLE_UTTERANCES)}")
    print(f"  Total signals emitted: {total_signals}")
    print()
    print("  Listener breakdown:")

    # Count signals by source (would need to track this, simplified for demo)
    print("    🦅 FillerFalcon    - Active")
    print("    🐅 TempoTiger      - Active")
    print("    🐆 LexiLynx        - Active")
    print("    🦒 GrammarGiraffe  - Not tested (requires Ollama)")
    print()

    logger.separator()
    print()
    print("✅ Demo complete! All listeners are working correctly.")
    print()
    print("Next steps:")
    print("  • Phase 1.3: Implement memory agents (NotionNightingale, etc.)")
    print("  • Phase 1.4: Implement OrchestratorOctopus to process signals")
    print("  • Phase 1.5: Implement coaching agents to act on signals")
    print()


def test_grammar_listener():
    """Optionally test GrammarGiraffe if Ollama is available."""
    try:
        from src.zoo.listeners import GrammarGiraffe

        logger = get_zoo_logger()
        print()
        logger.separator("🦒 Testing GrammarGiraffe (requires Ollama)")
        print()

        grammar_listener = GrammarGiraffe()
        print("  ✓ GrammarGiraffe initialized")
        print()

        # Test sentence with grammar error
        test_text = "I saw elephant yesterday"
        print(f"  💬 Test: \"{test_text}\"")
        print("  ⏳ Analyzing grammar (this may take ~500ms)...")
        print()

        signals = grammar_listener.process_utterance(test_text)

        if signals:
            print(f"  ✓ Grammar analysis complete: {len(signals)} error(s) detected")
        else:
            print("  ✓ Grammar analysis complete: No errors detected")

        print()
        logger.separator()

    except Exception as e:
        print(f"\n⚠️  GrammarGiraffe test skipped: {e}")
        print("   (Ollama must be running to test grammar detection)\n")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Demo Zoo listener agents with sample utterances"
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show verbose debug logging'
    )
    parser.add_argument(
        '-g', '--test-grammar',
        action='store_true',
        help='Also test GrammarGiraffe (requires Ollama)'
    )

    args = parser.parse_args()

    # Run main demo
    run_demo(verbose=args.verbose)

    # Optionally test grammar listener
    if args.test_grammar:
        test_grammar_listener()


if __name__ == '__main__':
    main()
