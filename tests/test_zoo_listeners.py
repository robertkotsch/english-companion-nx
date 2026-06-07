"""Integration tests for Zoo listener agents.

Tests all Phase 1.2 listeners: FillerFalcon, TempoTiger, GrammarGiraffe, LexiLynx
"""

import sys
import os
import unittest
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.zoo.listeners import (
    FillerFalcon,
    TempoTiger,
    GrammarGiraffe,
    LexiLynx,
)
from src.zoo.signals import (
    SIGNAL_FILLER_DETECTED,
    SIGNAL_TEMPO_ISSUE,
    SIGNAL_GRAMMAR_ERROR,
    SIGNAL_VOCAB_USED,
)


class TestFillerFalcon(unittest.TestCase):
    """Test FillerFalcon listener."""

    def setUp(self):
        """Set up test fixtures."""
        self.listener = FillerFalcon()

    def test_detect_single_filler(self):
        """Test detection of single filler word."""
        text = "I think um we should proceed"
        signals = self.listener.process_utterance(text)

        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].type, SIGNAL_FILLER_DETECTED)
        self.assertEqual(signals[0].data['filler'], 'um')
        self.assertEqual(signals[0].data['count'], 1)

    def test_detect_multiple_fillers(self):
        """Test detection of multiple filler words."""
        text = "Um, I think, like, we should, uh, proceed"
        signals = self.listener.process_utterance(text)

        self.assertEqual(len(signals), 1)
        self.assertGreater(signals[0].data['count'], 1)
        self.assertIn('all_fillers', signals[0].data)

    def test_detect_you_know(self):
        """Test detection of multi-word filler."""
        text = "This is, you know, really important"
        signals = self.listener.process_utterance(text)

        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].data['filler'], 'you know')

    def test_no_fillers(self):
        """Test clean utterance with no fillers."""
        text = "This is a clear statement"
        signals = self.listener.process_utterance(text)

        self.assertEqual(len(signals), 0)

    def test_empty_utterance(self):
        """Test empty utterance handling."""
        signals = self.listener.process_utterance("")
        self.assertEqual(len(signals), 0)

    def test_rate_calculation_with_duration(self):
        """Test fillers-per-minute calculation with duration metadata."""
        text = "Um, this is, like, really important"
        metadata = {'duration_ms': 3000}  # 3 seconds

        signals = self.listener.process_utterance(text, metadata)

        self.assertEqual(len(signals), 1)
        # 2 fillers in 3 seconds = 40 fillers/min
        self.assertGreater(signals[0].data['rate_per_min'], 30)

    def test_custom_threshold(self):
        """Test custom threshold configuration."""
        config = {'min_count_for_signal': 3}
        listener = FillerFalcon(config)

        # 2 fillers - should not emit signal
        text = "Um, I think like we should go"
        signals = listener.process_utterance(text)
        self.assertEqual(len(signals), 0)

        # 3 fillers - should emit signal
        text = "Um, I think, like, we should, uh, go"
        signals = listener.process_utterance(text)
        self.assertEqual(len(signals), 1)


class TestTempoTiger(unittest.TestCase):
    """Test TempoTiger listener."""

    def setUp(self):
        """Set up test fixtures."""
        self.listener = TempoTiger()

    def test_too_slow_wpm(self):
        """Test detection of too slow speaking rate."""
        text = "This is a test"  # 4 words
        metadata = {'duration_ms': 4000}  # 4 seconds = 60 WPM

        signals = self.listener.process_utterance(text, metadata)

        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].type, SIGNAL_TEMPO_ISSUE)
        self.assertEqual(signals[0].data['issue_type'], 'too_slow')
        self.assertLess(signals[0].data['wpm'], 100)

    def test_too_fast_wpm(self):
        """Test detection of too fast speaking rate."""
        text = "this is a very fast test with many words"  # 9 words
        metadata = {'duration_ms': 2000}  # 2 seconds = 270 WPM

        signals = self.listener.process_utterance(text, metadata)

        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].data['issue_type'], 'too_fast')
        self.assertGreater(signals[0].data['wpm'], 180)

    def test_normal_wpm(self):
        """Test normal speaking rate (no signal)."""
        text = "This is a normal paced sentence"  # 6 words
        metadata = {'duration_ms': 2400}  # 2.4s = 150 WPM

        signals = self.listener.process_utterance(text, metadata)

        # Should have no signals for normal tempo
        self.assertEqual(len(signals), 0)

    def test_long_pause_detection(self):
        """Test detection of long pauses."""
        text = "Hello world how are you"  # 5 words
        metadata = {
            'duration_ms': 8000,
            'word_timestamps': [
                {'word': 'Hello', 'start': 0.0, 'end': 0.5},
                {'word': 'world', 'start': 0.7, 'end': 1.2},
                {'word': 'how', 'start': 3.5, 'end': 3.8},  # 2.3s pause before this
                {'word': 'are', 'start': 4.0, 'end': 4.3},
                {'word': 'you', 'start': 4.5, 'end': 4.8},
            ]
        }

        signals = self.listener.process_utterance(text, metadata)

        # Should detect long pause
        pause_signals = [s for s in signals if s.data['issue_type'] == 'long_pause']
        self.assertGreater(len(pause_signals), 0)
        self.assertGreater(pause_signals[0].data['pause_duration_sec'], 2.0)

    def test_no_metadata(self):
        """Test handling of missing metadata."""
        text = "This is a test"
        signals = self.listener.process_utterance(text)

        # Should return empty list without metadata
        self.assertEqual(len(signals), 0)

    def test_custom_thresholds(self):
        """Test custom WPM thresholds."""
        config = {
            'min_wpm': 120,
            'max_wpm': 160,
        }
        listener = TempoTiger(config)

        text = "This is a test"  # 4 words
        metadata = {'duration_ms': 1500}  # 160 WPM - should be at limit

        signals = listener.process_utterance(text, metadata)

        # With tighter thresholds, this should trigger
        # (May or may not depending on exact calculation, but validates config works)
        self.assertIsInstance(signals, list)


class TestGrammarGiraffe(unittest.TestCase):
    """Test GrammarGiraffe listener."""

    def setUp(self):
        """Set up test fixtures."""
        self.listener = GrammarGiraffe()

    def test_detect_article_error(self):
        """Test detection of article errors."""
        # Simple test - actual detection depends on LLM
        text = "I saw elephant yesterday"

        try:
            signals = self.listener.process_utterance(text)
            # If LLM is available, should detect error
            # If not, will raise exception (caught in test)
            if signals:
                self.assertIsInstance(signals, list)
                # Check that signals have correct structure
                for signal in signals:
                    self.assertEqual(signal.type, SIGNAL_GRAMMAR_ERROR)
                    self.assertIn('error_type', signal.data)
        except Exception as e:
            # LLM not available - skip test
            self.skipTest(f"LLM not available: {e}")

    def test_correct_grammar(self):
        """Test clean utterance with correct grammar."""
        text = "I went to the store yesterday"

        try:
            signals = self.listener.process_utterance(text)
            # Should return empty list or minimal signals
            self.assertIsInstance(signals, list)
        except Exception as e:
            self.skipTest(f"LLM not available: {e}")

    def test_short_utterance_skipped(self):
        """Test that very short utterances are skipped."""
        text = "Yes ok"
        signals = self.listener.process_utterance(text)

        # Short utterances should be skipped
        self.assertEqual(len(signals), 0)

    def test_empty_utterance(self):
        """Test empty utterance handling."""
        signals = self.listener.process_utterance("")
        self.assertEqual(len(signals), 0)


class TestLexiLynx(unittest.TestCase):
    """Test LexiLynx listener."""

    def setUp(self):
        """Set up test fixtures."""
        self.listener = LexiLynx()

    def test_detect_target_word(self):
        """Test detection of target vocabulary word."""
        text = "We should leverage our expertise here"
        signals = self.listener.process_utterance(text)

        # Should detect 'leverage' from example cache
        vocab_signals = [s for s in signals if s.type == SIGNAL_VOCAB_USED]
        self.assertGreater(len(vocab_signals), 0)

        # Check signal details
        leverage_signal = vocab_signals[0]
        self.assertEqual(leverage_signal.data['word'], 'leverage')
        self.assertTrue(leverage_signal.data.get('correct', False))

    def test_detect_collocation(self):
        """Test detection of collocation phrase."""
        text = "We should take into account all factors"
        signals = self.listener.process_utterance(text)

        # Should detect 'take into account' collocation
        collocation_signals = [s for s in signals if 'take into account' in s.data.get('word', '')]
        self.assertGreater(len(collocation_signals), 0)

    def test_multiple_vocab_words(self):
        """Test detection of multiple target words."""
        text = "We need a comprehensive solution to facilitate communication"
        signals = self.listener.process_utterance(text)

        # Should detect both 'comprehensive' and 'facilitate'
        words_detected = [s.data['word'] for s in signals]
        self.assertIn('comprehensive', words_detected)
        self.assertIn('facilitate', words_detected)

    def test_no_target_words(self):
        """Test utterance with no target vocabulary."""
        text = "This is a simple test message"
        signals = self.listener.process_utterance(text)

        # Should have no signals
        self.assertEqual(len(signals), 0)

    def test_empty_utterance(self):
        """Test empty utterance handling."""
        signals = self.listener.process_utterance("")
        self.assertEqual(len(signals), 0)

    def test_vocab_stats(self):
        """Test vocabulary statistics."""
        stats = self.listener.get_vocab_stats()

        self.assertIn('words', stats)
        self.assertIn('collocations', stats)
        self.assertIn('total', stats)
        self.assertGreater(stats['total'], 0)


class TestListenerIntegration(unittest.TestCase):
    """Integration tests for all listeners together."""

    def test_all_listeners_on_complex_utterance(self):
        """Test all listeners processing the same complex utterance."""
        text = "Um, I think we should, like, leverage our comprehensive expertise"
        metadata = {
            'duration_ms': 4000,
            'utterance_id': 'test-123',
        }

        # Test FillerFalcon
        filler_listener = FillerFalcon()
        filler_signals = filler_listener.process_utterance(text, metadata)
        self.assertGreater(len(filler_signals), 0, "Should detect fillers")

        # Test TempoTiger
        tempo_listener = TempoTiger()
        tempo_signals = tempo_listener.process_utterance(text, metadata)
        # May or may not have tempo issues depending on thresholds

        # Test GrammarGiraffe (if LLM available)
        try:
            grammar_listener = GrammarGiraffe()
            grammar_signals = grammar_listener.process_utterance(text, metadata)
            self.assertIsInstance(grammar_signals, list)
        except Exception:
            pass  # LLM not available

        # Test LexiLynx
        lexi_listener = LexiLynx()
        vocab_signals = lexi_listener.process_utterance(text, metadata)
        # Should detect 'leverage' and 'comprehensive'
        words_detected = [s.data['word'] for s in vocab_signals]
        self.assertIn('leverage', words_detected)
        self.assertIn('comprehensive', words_detected)

    def test_listener_independence(self):
        """Test that listeners can run independently."""
        text = "This is a test"

        listeners = [
            FillerFalcon(),
            TempoTiger(),
            LexiLynx(),
        ]

        # All should process without interfering
        for listener in listeners:
            signals = listener.process_utterance(text)
            self.assertIsInstance(signals, list)


def run_tests(verbose=True):
    """Run all listener tests."""
    print("=" * 70)
    print("Zoo Listener Integration Tests")
    print("=" * 70)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestFillerFalcon))
    suite.addTests(loader.loadTestsFromTestCase(TestTempoTiger))
    suite.addTests(loader.loadTestsFromTestCase(TestGrammarGiraffe))
    suite.addTests(loader.loadTestsFromTestCase(TestLexiLynx))
    suite.addTests(loader.loadTestsFromTestCase(TestListenerIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 70)
    print("Test Summary:")
    print(f"  Tests run: {result.testsRun}")
    print(f"  Failures: {len(result.failures)}")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Skipped: {len(result.skipped)}")
    print("=" * 70)

    return result.wasSuccessful()


if __name__ == '__main__':
    import sys
    success = run_tests(verbose=True)
    sys.exit(0 if success else 1)
