"""Simple standalone tests for Zoo listeners (no dependencies).

Tests basic functionality without requiring full venv or LLM.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Test imports and basic functionality
def test_imports():
    """Test that all listeners can be imported."""
    print("Testing imports...")
    try:
        from src.zoo.listeners.filler_falcon import FillerFalcon
        from src.zoo.listeners.tempo_tiger import TempoTiger
        from src.zoo.listeners.lexi_lynx import LexiLynx
        print("✓ All listeners imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_filler_falcon():
    """Test FillerFalcon basic functionality."""
    print("\nTesting FillerFalcon...")
    try:
        from src.zoo.listeners.filler_falcon import FillerFalcon

        listener = FillerFalcon()

        # Test with fillers
        text = "Um, I think, like, we should proceed"
        signals = listener.process_utterance(text)

        assert len(signals) > 0, "Should detect fillers"
        assert signals[0].type == "filler_detected", "Signal type should be filler_detected"
        assert signals[0].data['count'] > 1, "Should count multiple fillers"

        print(f"✓ Detected {signals[0].data['count']} fillers")
        print(f"  Filler rate: {signals[0].data['rate_per_min']:.1f}/min")

        # Test without fillers
        text_clean = "This is a clear statement"
        signals_clean = listener.process_utterance(text_clean)
        assert len(signals_clean) == 0, "Should not detect fillers in clean text"

        print("✓ FillerFalcon working correctly")
        return True

    except Exception as e:
        print(f"✗ FillerFalcon test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tempo_tiger():
    """Test TempoTiger basic functionality."""
    print("\nTesting TempoTiger...")
    try:
        from src.zoo.listeners.tempo_tiger import TempoTiger

        listener = TempoTiger()

        # Test too slow
        text = "This is a test"
        metadata = {'duration_ms': 4000}  # 60 WPM - too slow
        signals = listener.process_utterance(text, metadata)

        assert len(signals) > 0, "Should detect slow tempo"
        assert signals[0].data['issue_type'] == 'too_slow', "Should flag as too slow"

        print(f"✓ Detected slow tempo: {signals[0].data['wpm']:.1f} WPM")

        # Test too fast
        text_fast = "this is a very fast test with many words"
        metadata_fast = {'duration_ms': 2000}  # 270 WPM - too fast
        signals_fast = listener.process_utterance(text_fast, metadata_fast)

        assert len(signals_fast) > 0, "Should detect fast tempo"
        assert signals_fast[0].data['issue_type'] == 'too_fast', "Should flag as too fast"

        print(f"✓ Detected fast tempo: {signals_fast[0].data['wpm']:.1f} WPM")

        print("✓ TempoTiger working correctly")
        return True

    except Exception as e:
        print(f"✗ TempoTiger test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_lexi_lynx():
    """Test LexiLynx basic functionality."""
    print("\nTesting LexiLynx...")
    try:
        from src.zoo.listeners.lexi_lynx import LexiLynx

        listener = LexiLynx()

        # Test vocab detection
        text = "We should leverage our comprehensive expertise"
        signals = listener.process_utterance(text)

        assert len(signals) > 0, "Should detect target vocab words"

        words_detected = [s.data['word'] for s in signals]
        assert 'leverage' in words_detected, "Should detect 'leverage'"
        assert 'comprehensive' in words_detected, "Should detect 'comprehensive'"

        print(f"✓ Detected {len(signals)} target vocabulary words:")
        for signal in signals:
            print(f"  - {signal.data['word']} ({signal.data.get('word_type', 'unknown')})")

        # Test stats
        stats = listener.get_vocab_stats()
        print(f"✓ Vocab cache: {stats['words']} words, {stats['collocations']} collocations")

        print("✓ LexiLynx working correctly")
        return True

    except Exception as e:
        print(f"✗ LexiLynx test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_signal_structure():
    """Test signal structure and methods."""
    print("\nTesting Signal structure...")
    try:
        from src.zoo.signals import Signal, create_filler_signal

        # Test basic signal creation
        signal = Signal(
            source="TestAgent",
            type="test_type",
            severity=0.5,
            scope="utterance",
            realtime_desirable=True,
            data={"test": "data"}
        )

        assert signal.source == "TestAgent"
        assert signal.severity == 0.5

        # Test to_dict
        signal_dict = signal.to_dict()
        assert "source" in signal_dict
        assert "type" in signal_dict

        # Test from_dict
        signal_restored = Signal.from_dict(signal_dict)
        assert signal_restored.source == signal.source

        # Test factory function
        filler_sig = create_filler_signal(
            source="FillerFalcon",
            filler_word="um",
            position=1,
            total_count=2,
            rate_per_min=5.0
        )
        assert filler_sig.type == "filler_detected"

        print("✓ Signal structure working correctly")
        return True

    except Exception as e:
        print(f"✗ Signal test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all simple tests."""
    print("=" * 70)
    print("Zoo Listeners - Simple Functionality Tests")
    print("=" * 70)

    tests = [
        test_imports,
        test_signal_structure,
        test_filler_falcon,
        test_tempo_tiger,
        test_lexi_lynx,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            results.append(False)

    print("\n" + "=" * 70)
    print("Summary:")
    print(f"  Passed: {sum(results)}/{len(results)}")
    print(f"  Failed: {len(results) - sum(results)}/{len(results)}")
    print("=" * 70)

    if all(results):
        print("\n✅ All tests passed! Phase 1.2 listeners are working correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Check output above for details.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
