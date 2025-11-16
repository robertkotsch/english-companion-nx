#!/usr/bin/env python3
"""Test GrammarGiraffe with different Ollama models.

Compare grammar detection accuracy between llama3.2:3b and llama3.2:8b models.

Usage:
    # Ensure both models are available:
    ollama pull llama3.2:3b
    ollama pull llama3.1:8b

    # Run comparison:
    python3 test_grammar_models.py
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.zoo.listeners.grammar_giraffe import GrammarGiraffe
from src.zoo.zoo_logger import get_zoo_logger, set_zoo_log_level
import logging


# Test utterances - mix of correct and incorrect grammar
TEST_UTTERANCES = [
    {
        'text': "This is an nice example.",
        'expected': 'error',  # Article error: "an" → "a"
        'description': "Article error (an → a)"
    },
    {
        'text': "What are the tools I would be using?",
        'expected': 'correct',  # Grammatically correct
        'description': "Correct grammar (should not flag)"
    },
    {
        'text': "Either you run your life, or life runs you",
        'expected': 'correct',  # Grammatically correct (Jim Rohn quote)
        'description': "Correct either...or construction"
    },
    {
        'text': "I saw elephant yesterday",
        'expected': 'error',  # Missing article
        'description': "Missing article before 'elephant'"
    },
    {
        'text': "She go to store every day",
        'expected': 'error',  # Subject-verb agreement
        'description': "Subject-verb agreement (go → goes)"
    },
    {
        'text': "What time is it?",
        'expected': 'correct',  # Correct
        'description': "Simple correct question"
    },
    {
        'text': "I am would using this tool",
        'expected': 'error',  # Double auxiliary
        'description': "Double auxiliary verbs error"
    },
    {
        'text': "The informations are helpful",
        'expected': 'error',  # Information is uncountable
        'description': "Uncountable noun (information)"
    },
]


def test_model(model_name: str, utterances: list) -> dict:
    """Test GrammarGiraffe with specific model.

    Args:
        model_name: Ollama model to use
        utterances: List of test utterances

    Returns:
        Dict with test results
    """
    print(f"\n{'='*70}")
    print(f"Testing with model: {model_name}")
    print(f"{'='*70}\n")

    # Initialize GrammarGiraffe with specified model
    config = {
        'llm_model': model_name,
        # Use lower thresholds to see what model detects
        'min_severity': 0.3,
        'category_thresholds': {
            'articles': 0.3,
            'pluralization': 0.3,
            'tense': 0.3,
            'subject_verb': 0.3,
            'word_order': 0.3,
            'prepositions': 0.3,
            'pronouns': 0.3,
        }
    }

    try:
        grammar = GrammarGiraffe(config)
        print(f"✓ Initialized with {model_name}\n")
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        return {'error': str(e)}

    results = {
        'model': model_name,
        'total': len(utterances),
        'correct_detections': 0,
        'false_positives': 0,
        'false_negatives': 0,
        'timings': [],
        'details': []
    }

    for i, test in enumerate(utterances, 1):
        text = test['text']
        expected = test['expected']
        description = test['description']

        print(f"Test {i}/{len(utterances)}: {description}")
        print(f"  Text: \"{text}\"")
        print(f"  Expected: {expected}")

        # Time the analysis
        start = time.time()
        try:
            signals = grammar.process_utterance(text)
            duration = time.time() - start
            results['timings'].append(duration)

            # Check result
            has_error = len(signals) > 0
            is_correct = (expected == 'error' and has_error) or \
                        (expected == 'correct' and not has_error)

            if is_correct:
                results['correct_detections'] += 1
                status = "✓ CORRECT"
            elif expected == 'error' and not has_error:
                results['false_negatives'] += 1
                status = "✗ FALSE NEGATIVE (missed error)"
            else:  # expected == 'correct' and has_error
                results['false_positives'] += 1
                status = "✗ FALSE POSITIVE (flagged correct sentence)"

            print(f"  Result: {status} ({duration:.2f}s)")

            if signals:
                for signal in signals:
                    print(f"    → {signal.data.get('error_type', 'unknown')}: "
                          f"severity={signal.severity:.2f} - "
                          f"{signal.data.get('explanation', '')}")

            results['details'].append({
                'text': text,
                'expected': expected,
                'detected': has_error,
                'correct': is_correct,
                'duration': duration,
                'signals': [s.to_dict() for s in signals]
            })

        except Exception as e:
            print(f"  Error: {e}")
            results['details'].append({
                'text': text,
                'error': str(e)
            })

        print()

    return results


def compare_models():
    """Compare multiple models."""
    print("\n" + "="*70)
    print("GRAMMAR MODEL COMPARISON TEST")
    print("="*70)
    print("\nTesting grammar detection with different model sizes...")
    print("This will help determine the best model for your use case.\n")

    models = ['llama3.2:3b', 'llama3.1:8b']
    all_results = []

    for model in models:
        results = test_model(model, TEST_UTTERANCES)
        if 'error' not in results:
            all_results.append(results)
        else:
            print(f"\n⚠️  Skipping {model} - not available or error occurred")
            print(f"   Run: ollama pull {model}")

    # Print comparison summary
    if len(all_results) >= 2:
        print("\n" + "="*70)
        print("COMPARISON SUMMARY")
        print("="*70 + "\n")

        for results in all_results:
            model = results['model']
            total = results['total']
            correct = results['correct_detections']
            fp = results['false_positives']
            fn = results['false_negatives']
            avg_time = sum(results['timings']) / len(results['timings']) if results['timings'] else 0

            accuracy = (correct / total * 100) if total > 0 else 0

            print(f"{model}:")
            print(f"  Accuracy: {accuracy:.1f}% ({correct}/{total} correct)")
            print(f"  False Positives: {fp}")
            print(f"  False Negatives: {fn}")
            print(f"  Avg Speed: {avg_time:.2f}s per utterance")
            print()

        # Recommendation
        print("="*70)
        print("RECOMMENDATION")
        print("="*70)
        print()

        if all_results[1]['correct_detections'] > all_results[0]['correct_detections']:
            print(f"✓ {all_results[1]['model']} has better accuracy")
            print(f"  Trade-off: ~{all_results[1]['timings'][0] - all_results[0]['timings'][0]:.1f}s slower")
            print()
            print("To use the better model, configure GrammarGiraffe:")
            print("  config = {'llm_model': 'llama3.2:8b'}")
            print("  grammar = GrammarGiraffe(config)")
        else:
            print(f"✓ {all_results[0]['model']} is sufficient")
            print(f"  Both models have similar accuracy, use faster 3b model")


if __name__ == '__main__':
    set_zoo_log_level(logging.WARNING)  # Reduce noise
    compare_models()
