#!/usr/bin/env python3
"""Interactive Zoo Listener Test - Enter your own utterances.

Test all Zoo listeners with your own input text.
Perfect for testing GrammarGiraffe with specific sentences on Jetson.

Usage:
    python3 test_zoo_interactive.py
    python3 test_zoo_interactive.py --verbose
    python3 test_zoo_interactive.py --no-grammar  # Skip GrammarGiraffe
"""

import sys
import logging
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.zoo.listeners import FillerFalcon, TempoTiger, LexiLynx
from src.zoo.zoo_logger import get_zoo_logger, set_zoo_log_level

# Try to import GrammarGiraffe (requires Ollama)
try:
    from src.zoo.listeners import GrammarGiraffe
    GRAMMAR_AVAILABLE = True
except ImportError:
    GRAMMAR_AVAILABLE = False


def print_header():
    """Print welcome header."""
    print("\n" + "="*70)
    print("🏞️  ZOO INTERACTIVE LISTENER TEST")
    print("="*70)
    print()
    print("Test all Zoo listeners with your own utterances!")
    print()
    print("Available listeners:")
    print("  🦅 FillerFalcon    - Detects filler words (um, uh, like, etc.)")
    print("  🐅 TempoTiger      - Analyzes speaking rate")
    print("  🐆 LexiLynx        - Tracks vocabulary usage")
    if GRAMMAR_AVAILABLE:
        print("  🦒 GrammarGiraffe  - Detects grammar errors (⚠️  ~500ms per utterance)")
    else:
        print("  🦒 GrammarGiraffe  - ❌ Not available (requires Ollama)")
    print()
    print("Commands:")
    print("  • Type your utterance and press Enter")
    print("  • 'quit' or 'exit' to exit")
    print("  • 'help' for this message")
    print("  • 'stats' to show vocabulary cache stats")
    print("="*70)
    print()


def print_help():
    """Print help message."""
    print()
    print("How to use:")
    print("  1. Enter your utterance text (e.g., 'Um, I think we should leverage this')")
    print("  2. Enter duration in seconds (optional - press Enter to skip)")
    print("  3. See what signals each listener emits!")
    print()
    print("Tips:")
    print("  • Include fillers (um, uh, like) to test FillerFalcon")
    print("  • Use vocabulary words (leverage, facilitate, comprehensive) for LexiLynx")
    print("  • Try grammar errors for GrammarGiraffe (e.g., 'I saw elephant')")
    print("  • Duration affects TempoTiger's WPM calculation")
    print()


def get_user_input():
    """Get utterance and metadata from user.

    Returns:
        Tuple of (text, metadata) or (None, None) if user wants to quit
    """
    # Get utterance text
    print("\n" + "-"*70)
    text = input("💬 Enter utterance (or 'quit' to exit): ").strip()

    if not text:
        print("⚠️  Empty input, please try again")
        return None, None

    # Check for commands
    text_lower = text.lower()
    if text_lower in ('quit', 'exit', 'q'):
        return "QUIT", None
    elif text_lower == 'help':
        return "HELP", None
    elif text_lower == 'stats':
        return "STATS", None

    # Get optional duration
    duration_input = input("⏱️  Duration in seconds (press Enter to skip): ").strip()

    duration_ms = None
    if duration_input:
        try:
            duration_sec = float(duration_input)
            duration_ms = int(duration_sec * 1000)
            print(f"   ✓ Using {duration_sec:.1f}s ({duration_ms}ms)")
        except ValueError:
            print("   ⚠️  Invalid duration, will estimate from word count")
    else:
        # Estimate duration from word count (assume ~150 WPM average)
        word_count = len(text.split())
        estimated_sec = (word_count / 150) * 60
        duration_ms = int(estimated_sec * 1000)
        print(f"   ℹ️  Estimated {estimated_sec:.1f}s based on {word_count} words")

    # Build metadata
    metadata = {
        'utterance_id': f'interactive-{int(time.time())}',
        'timestamp': time.time(),
        'duration_ms': duration_ms,
    }

    return text, metadata


def process_utterance(text, metadata, listeners, use_grammar=True):
    """Process utterance through all listeners.

    Args:
        text: Utterance text
        metadata: Utterance metadata
        listeners: Dict of listener instances
        use_grammar: Whether to use GrammarGiraffe

    Returns:
        List of all signals
    """
    logger = get_zoo_logger()

    print()
    logger.separator("Processing")
    print()

    all_signals = []

    # FillerFalcon
    print("🦅 FillerFalcon analyzing...")
    filler_signals = listeners['filler'].process_utterance(text, metadata)
    all_signals.extend(filler_signals)

    # TempoTiger
    print("🐅 TempoTiger analyzing...")
    tempo_signals = listeners['tempo'].process_utterance(text, metadata)
    all_signals.extend(tempo_signals)

    # LexiLynx
    print("🐆 LexiLynx analyzing...")
    vocab_signals = listeners['vocab'].process_utterance(text, metadata)
    all_signals.extend(vocab_signals)

    # GrammarGiraffe (if available and enabled)
    if use_grammar and GRAMMAR_AVAILABLE and 'grammar' in listeners:
        print("🦒 GrammarGiraffe analyzing (this may take ~500ms)...")
        grammar_signals = listeners['grammar'].process_utterance(text, metadata)
        all_signals.extend(grammar_signals)

    print()
    logger.separator()
    print()

    # Summary
    if all_signals:
        print(f"📊 Total signals: {len(all_signals)}")
        print()
        print("Signal breakdown:")
        for signal in all_signals:
            severity_icon = "🔴" if signal.severity > 0.7 else "🟡" if signal.severity > 0.4 else "🟢"
            print(f"  {severity_icon} {signal.source}: {signal.type} (severity: {signal.severity:.2f})")
            if 'explanation' in signal.data:
                print(f"     └─ {signal.data['explanation']}")
            elif 'issue_type' in signal.data:
                print(f"     └─ {signal.data['issue_type']}")
    else:
        print("✅ No issues detected - clean utterance!")

    return all_signals


def show_stats(vocab_listener):
    """Show vocabulary cache statistics."""
    print()
    print("="*70)
    print("📊 Vocabulary Cache Statistics")
    print("="*70)

    stats = vocab_listener.get_vocab_stats()
    print(f"  Words: {stats['words']}")
    print(f"  Collocations: {stats['collocations']}")
    print(f"  Total: {stats['total']}")
    print()

    # Show sample words
    if vocab_listener.vocab_data.get('words'):
        print("Sample vocabulary words:")
        for word_entry in vocab_listener.vocab_data['words'][:5]:
            print(f"  • {word_entry['word']} ({word_entry['type']})")

    if vocab_listener.vocab_data.get('collocations'):
        print()
        print("Sample collocations:")
        for coll_entry in vocab_listener.vocab_data['collocations'][:3]:
            print(f"  • {coll_entry['phrase']}")

    print("="*70)


def main():
    """Main interactive loop."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Interactive test for Zoo listeners"
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show verbose debug logging'
    )
    parser.add_argument(
        '--no-grammar',
        action='store_true',
        help='Skip GrammarGiraffe (faster testing)'
    )
    parser.add_argument(
        '--grammar-model',
        type=str,
        default='llama3.2:3b',
        help='Ollama model for GrammarGiraffe (default: llama3.2:3b, try: llama3.1:8b for better accuracy)'
    )

    args = parser.parse_args()

    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    set_zoo_log_level(log_level)
    logger = get_zoo_logger()

    # Print header
    print_header()

    # Initialize listeners
    print("📦 Initializing listeners...")
    listeners = {
        'filler': FillerFalcon(),
        'tempo': TempoTiger(),
        'vocab': LexiLynx(),
    }

    if GRAMMAR_AVAILABLE and not args.no_grammar:
        try:
            grammar_config = {'llm_model': args.grammar_model}
            listeners['grammar'] = GrammarGiraffe(grammar_config)
            print(f"  ✓ All listeners ready (GrammarGiraffe using {args.grammar_model})")
        except Exception as e:
            print(f"  ⚠️  GrammarGiraffe failed to initialize: {e}")
            print("  ✓ Other listeners ready")
    else:
        if args.no_grammar:
            print("  ✓ Listeners ready (GrammarGiraffe skipped by --no-grammar)")
        else:
            print("  ✓ Listeners ready (GrammarGiraffe not available)")

    print()
    print("Ready! Enter your first utterance below.")

    # Interactive loop
    utterance_count = 0
    total_signals = 0

    while True:
        try:
            # Get user input
            text, metadata = get_user_input()

            if text is None:
                continue

            # Handle commands
            if text == "QUIT":
                break
            elif text == "HELP":
                print_help()
                continue
            elif text == "STATS":
                show_stats(listeners['vocab'])
                continue

            # Process utterance
            utterance_count += 1
            print(f"\n📝 Utterance #{utterance_count}")
            print(f"   Text: \"{text}\"")

            use_grammar = GRAMMAR_AVAILABLE and not args.no_grammar and 'grammar' in listeners
            signals = process_utterance(text, metadata, listeners, use_grammar)
            total_signals += len(signals)

        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            if args.verbose:
                traceback.print_exc()
            print("Continuing...\n")

    # Exit summary
    print()
    logger.separator("Session Summary")
    print()
    print(f"  Utterances tested: {utterance_count}")
    print(f"  Total signals: {total_signals}")
    if utterance_count > 0:
        print(f"  Average signals/utterance: {total_signals/utterance_count:.1f}")
    print()
    print("Thank you for testing the Zoo listeners! 🏞️")
    print()


if __name__ == '__main__':
    main()
