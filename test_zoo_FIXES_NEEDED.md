# Quick Fix Instructions for test_zoo_dry_run_all_agents.py

The test file has a few remaining issues that need manual fixing:

## Issue 1: OrchestratorOctopus test (Line 467-472)

**Current (broken):**
```python
            # Test with real signals
            print(f"   🎬 Action: {action.type.value}")  # action is not defined!
            print(f"   📝 Reason: {action.reason}")
```

**Should be:**
```python
            # Test with real signals
            self.print_test("OrchestratorOctopus", "Process real signals")
            
            # Create real signals
            signals = [
                create_filler_signal("FillerFalcon", "um", 1, 3, 6.0),
                create_grammar_signal("GrammarGiraffe", "tense", 0.8, "went", "gone", explanation="Should use 'went'")
            ]
            
            utterance = "Um, I have went to the store"
            action = orchestrator.process_utterance(utterance, signals)
            
            print(f"   🎬 Action: {action.type.value}")
            print(f"   📝 Reason: {action.reason}")
```

## Issue 2: grammar_signal factory call signature (Line 99)

**Current:**
```python
grammar_sig = create_grammar_signal("GrammarGiraffe", "article", "a/an", "Should use 'an'", 0.7)
```

**Should be:**
```python
grammar_sig = create_grammar_signal("GrammarGiraffe", "article", 0.7, "a", "an", explanation="Should use 'an'")
```

## Quick Fix Command

Run this on Jetson to apply the fixes:

```bash
cd ~/apps/english-companion-nx

# Fix line 99 - grammar signal factory
sed -i '99s/create_grammar_signal("GrammarGiraffe", "article", "a\/an", "Should use '\''an'\''", 0.7)/create_grammar_signal("GrammarGiraffe", "article", 0.7, "a", "an", explanation="Should use '\''an'\''")/' test_zoo_dry_run_all_agents.py

# The Orchestrator test fix is more complex, easier to do manually in editor
# Or just comment out lines 468-472 and add the correct code
```

## Manual Fix (Recommended)

Open the file in an editor and:
1. Go to line 467
2. Replace lines 467-472 with the corrected code shown above
3. Save and run the test again
