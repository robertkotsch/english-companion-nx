"""LexiLynx - Vocabulary usage tracking listener.

Tracks usage of target vocabulary words from Notion database.
Detects correct usage, missed opportunities, and incorrect usage.
"""

import json
import os
from pathlib import Path
from typing import List, Optional, Dict, Any, Set
from .base import BaseListener, ListenerProcessingError
from ..signals import Signal, create_vocab_signal, SIGNAL_VOCAB_USED, SIGNAL_VOCAB_OPPORTUNITY
from ..zoo_logger import get_zoo_logger


class LexiLynx(BaseListener):
    """Tracks vocabulary usage against target word list.

    Loads vocabulary from local cache (populated by NotionNightingale)
    and matches against user utterances.

    Configuration:
        vocab_cache_path: str - Path to vocab JSON cache (default: data/vocab/cache.json)
        match_threshold: float - Similarity threshold for fuzzy matching (default: 0.8)
        check_collocations: bool - Also check for multi-word phrases (default: True)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize LexiLynx.

        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config)

        # Get vocab cache path
        default_cache = "data/vocab/cache.json"
        self.vocab_cache_path = self.get_config_value('vocab_cache_path', default_cache)

        # Configuration
        self.match_threshold = self.get_config_value('match_threshold', 0.8)
        self.check_collocations = self.get_config_value('check_collocations', True)

        # Load vocabulary cache
        self.vocab_data = self._load_vocab_cache()

        # Build lookup structures for efficient matching
        self.target_words = self._build_word_set()
        self.collocations = self._build_collocation_set()

        # Get logger
        self.logger = get_zoo_logger()

    def process_utterance(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Signal]:
        """Track vocabulary usage in utterance.

        Args:
            text: User's utterance text
            metadata: Optional metadata (not used currently)

        Returns:
            List of vocabulary-related signals
        """
        if not text or not text.strip():
            return []

        if not self.vocab_data:
            # No vocabulary loaded - skip processing
            return []

        try:
            signals = []

            # Normalize text for matching
            text_lower = text.lower()
            words = text_lower.split()

            # Check for target word usage
            word_signals = self._check_word_usage(text_lower, words)
            signals.extend(word_signals)

            # Check for collocation usage
            if self.check_collocations:
                collocation_signals = self._check_collocation_usage(text_lower)
                signals.extend(collocation_signals)

            # Log results
            if signals:
                words_used = [s.data['word'] for s in signals]
                detail = f"Used: {', '.join(words_used)}"
                for signal in signals:
                    self.logger.listener_signal(self.name, signal.type, signal.severity,
                                               f"{signal.data['word']} ({signal.data.get('word_type', 'unknown')})")
            else:
                self.logger.listener_no_signal(self.name)

            return signals

        except Exception as e:
            raise ListenerProcessingError(
                f"LexiLynx failed to process utterance: {e}"
            ) from e

    def _load_vocab_cache(self) -> Dict[str, Any]:
        """Load vocabulary cache from JSON file.

        Returns:
            Vocabulary data dictionary or empty dict if file not found
        """
        cache_path = Path(self.vocab_cache_path)

        if not cache_path.exists():
            # No cache file yet - this is OK for initial setup
            # NotionNightingale will populate it later
            return {"words": [], "collocations": []}

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            # Cache file corrupted - log warning but continue
            # In production, we'd log this properly
            return {"words": [], "collocations": []}

    def _build_word_set(self) -> Set[str]:
        """Build set of target words for fast lookup.

        Returns:
            Set of lowercase target words
        """
        words = set()
        for entry in self.vocab_data.get('words', []):
            word = entry.get('word', '').lower()
            if word:
                words.add(word)
        return words

    def _build_collocation_set(self) -> Set[str]:
        """Build set of target collocations/phrases.

        Returns:
            Set of lowercase collocation phrases
        """
        collocations = set()
        for entry in self.vocab_data.get('collocations', []):
            phrase = entry.get('phrase', '').lower()
            if phrase:
                collocations.add(phrase)
        return collocations

    def _check_word_usage(
        self,
        text_lower: str,
        words: List[str]
    ) -> List[Signal]:
        """Check for target word usage.

        Args:
            text_lower: Lowercase utterance text
            words: List of words in utterance

        Returns:
            List of vocab_used signals
        """
        signals = []

        for word in words:
            # Clean word (remove punctuation)
            clean_word = word.strip('.,!?;:"\'-')

            if clean_word in self.target_words:
                # Target word used!
                # For MVP, we assume correct usage
                # In future, could use LLM to verify context appropriateness

                # Find full word entry for details
                word_entry = self._get_word_entry(clean_word)

                signal = create_vocab_signal(
                    source=self.name,
                    signal_type=SIGNAL_VOCAB_USED,
                    word=clean_word,
                    severity=0.0,  # Not an error, just tracking
                    correct=True,  # Assume correct for now
                    word_type=word_entry.get('type', 'unknown'),
                    definition=word_entry.get('definition', ''),
                )
                signals.append(signal)

        return signals

    def _check_collocation_usage(self, text_lower: str) -> List[Signal]:
        """Check for target collocation usage.

        Args:
            text_lower: Lowercase utterance text

        Returns:
            List of vocab_used signals for collocations
        """
        signals = []

        for collocation in self.collocations:
            if collocation in text_lower:
                # Collocation used!
                collocation_entry = self._get_collocation_entry(collocation)

                signal = create_vocab_signal(
                    source=self.name,
                    signal_type=SIGNAL_VOCAB_USED,
                    word=collocation,
                    severity=0.0,
                    correct=True,
                    word_type='collocation',
                    definition=collocation_entry.get('meaning', ''),
                )
                signals.append(signal)

        return signals

    def _get_word_entry(self, word: str) -> Dict[str, Any]:
        """Get full word entry from cache.

        Args:
            word: Target word (lowercase)

        Returns:
            Word entry dictionary or empty dict
        """
        for entry in self.vocab_data.get('words', []):
            if entry.get('word', '').lower() == word:
                return entry
        return {}

    def _get_collocation_entry(self, phrase: str) -> Dict[str, Any]:
        """Get full collocation entry from cache.

        Args:
            phrase: Collocation phrase (lowercase)

        Returns:
            Collocation entry dictionary or empty dict
        """
        for entry in self.vocab_data.get('collocations', []):
            if entry.get('phrase', '').lower() == phrase:
                return entry
        return {}

    def reload_cache(self) -> bool:
        """Reload vocabulary cache from disk.

        Useful when NotionNightingale updates the cache.

        Returns:
            True if reload successful
        """
        try:
            self.vocab_data = self._load_vocab_cache()
            self.target_words = self._build_word_set()
            self.collocations = self._build_collocation_set()
            return True
        except Exception:
            return False

    def get_vocab_stats(self) -> Dict[str, int]:
        """Get vocabulary cache statistics.

        Returns:
            Dictionary with word and collocation counts
        """
        return {
            'words': len(self.target_words),
            'collocations': len(self.collocations),
            'total': len(self.target_words) + len(self.collocations),
        }
