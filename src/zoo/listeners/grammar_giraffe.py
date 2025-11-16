"""GrammarGiraffe - Grammar error detection listener.

Uses LLM-based analysis to detect grammar errors in user utterances.
Focuses on common error categories like articles, tense, word order, etc.
"""

import json
from typing import List, Optional, Dict, Any
from .base import BaseListener, ListenerProcessingError
from ..signals import Signal, create_grammar_signal
from ..zoo_logger import get_zoo_logger
from src.conversation.llm_client import OllamaClient


class GrammarGiraffe(BaseListener):
    """Detects grammar errors using LLM analysis.

    Analyzes user utterances for common grammar mistakes and emits
    signals with error categorization and correction suggestions.

    Configuration:
        min_severity: float - Minimum severity to emit signal (default: 0.3)
        llm_temperature: float - LLM temperature for analysis (default: 0.2)
        categories: List[str] - Grammar categories to check (default: all)
    """

    # Grammar error categories to detect
    GRAMMAR_CATEGORIES = [
        "articles",           # a/an/the usage
        "tense",             # verb tense errors
        "word_order",        # incorrect word order
        "subject_verb",      # subject-verb agreement
        "prepositions",      # incorrect preposition usage
        "pluralization",     # singular/plural errors
        "pronouns",          # pronoun errors
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize GrammarGiraffe.

        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config)

        # Initialize LLM client
        self.llm_client = OllamaClient()

        # Configuration
        self.min_severity = self.get_config_value('min_severity', 0.6)  # Default threshold
        self.llm_temperature = self.get_config_value('llm_temperature', 0.2)
        self.categories = self.get_config_value('categories', self.GRAMMAR_CATEGORIES)

        # Category-specific thresholds (more reliable categories = lower threshold)
        self.category_thresholds = self.get_config_value('category_thresholds', {
            'articles': 0.5,         # Articles are usually clear (a/an/the)
            'pluralization': 0.6,    # Singular/plural is usually clear
            'tense': 0.7,            # Tense can be subjective/contextual
            'subject_verb': 0.75,    # High false positive rate
            'word_order': 0.7,       # Can be stylistic
            'prepositions': 0.7,     # Often contextual/idiomatic
            'pronouns': 0.6,         # Usually clear
        })

        # Get logger
        self.logger = get_zoo_logger()

    def process_utterance(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Signal]:
        """Analyze utterance for grammar errors.

        Args:
            text: User's utterance text
            metadata: Optional metadata (not used currently)

        Returns:
            List of grammar error signals
        """
        if not text or not text.strip():
            return []

        # Skip very short utterances (likely interjections)
        if len(text.split()) < 3:
            return []

        try:
            # Analyze grammar using LLM
            errors = self._analyze_grammar(text)

            # Convert errors to signals
            signals = []
            for error in errors:
                severity = error.get('severity', 0.5)
                error_category = error.get('category', 'unknown')

                # Get category-specific threshold, or use default
                threshold = self.category_thresholds.get(error_category, self.min_severity)

                # Only emit signal if severity exceeds category threshold
                if severity <= threshold:
                    continue

                signal = create_grammar_signal(
                    source=self.name,
                    error_type=error.get('category', 'unknown'),
                    severity=severity,
                    original=error.get('original', ''),
                    suggestion=error.get('suggestion', ''),
                    explanation=error.get('explanation', ''),
                )
                signals.append(signal)

                # Log signal
                detail = f"{error.get('category', 'unknown')}: {error.get('explanation', '')}"
                self.logger.listener_signal(self.name, signal.type, signal.severity, detail)

            if not signals:
                self.logger.listener_no_signal(self.name)

            return signals

        except Exception as e:
            # Log error but don't crash - grammar analysis is non-critical
            # In production, we'd log this properly
            raise ListenerProcessingError(
                f"GrammarGiraffe failed to process utterance: {e}"
            ) from e

    def _analyze_grammar(self, text: str) -> List[Dict[str, Any]]:
        """Use LLM to analyze grammar.

        Args:
            text: User's utterance

        Returns:
            List of error dictionaries with keys:
                - category: Error type (articles, tense, etc.)
                - severity: 0.0-1.0 (how serious the error is)
                - original: The problematic text
                - suggestion: Suggested correction
                - explanation: Brief explanation
        """
        # Build grammar analysis prompt
        prompt = self._build_grammar_prompt(text)

        # Call LLM
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a conservative grammar analysis assistant. Analyze English utterances "
                    "for CLEAR, UNAMBIGUOUS grammar errors and respond ONLY with valid JSON. "
                    "Be conservative - only flag obvious errors. Do NOT flag colloquial speech, "
                    "questions, or statements that are grammatically acceptable. "
                    "When in doubt, return empty array []."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        response = self.llm_client.chat(
            messages=messages,
            temperature=self.llm_temperature,
            max_tokens=500
        )

        # Parse LLM response
        errors = self._parse_grammar_response(response)

        return errors

    def _build_grammar_prompt(self, text: str) -> str:
        """Build grammar analysis prompt.

        Args:
            text: User's utterance

        Returns:
            Formatted prompt string
        """
        categories_str = ", ".join(self.categories)

        prompt = f"""Analyze this English utterance for ACTUAL grammar errors:

"{text}"

IMPORTANT: Only flag CLEAR, UNAMBIGUOUS errors. Do NOT flag:
- Colloquial or informal speech (that's acceptable)
- Questions or statements that are grammatically correct
- Style preferences or minor word choices

Check for errors in these categories: {categories_str}

Respond with a JSON array of errors. Each error should have:
- category: error type (articles, tense, word_order, subject_verb, prepositions, pluralization, pronouns)
- severity: 0.0-1.0 (0.5=moderate, 0.7=significant, 0.9=critical) - Use HIGH severity only for clear errors
- original: the problematic phrase
- suggestion: corrected version
- explanation: brief reason (max 10 words)

If no CLEAR errors found, return empty array: []

Example response format:
[
  {{
    "category": "articles",
    "severity": 0.6,
    "original": "I saw elephant",
    "suggestion": "I saw an elephant",
    "explanation": "Missing article before vowel sound"
  }}
]

IMPORTANT: Return ONLY the JSON array, no other text."""

        return prompt

    def _parse_grammar_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response into error list.

        Args:
            response: LLM response text (should be JSON)

        Returns:
            List of error dictionaries
        """
        # Clean response - LLMs sometimes add markdown code blocks
        response = response.strip()

        # Remove markdown code blocks if present
        if response.startswith('```'):
            # Extract JSON from code block
            lines = response.split('\n')
            json_lines = []
            in_code_block = False

            for line in lines:
                if line.startswith('```'):
                    in_code_block = not in_code_block
                    continue
                if in_code_block or (not line.startswith('```')):
                    json_lines.append(line)

            response = '\n'.join(json_lines).strip()

        try:
            errors = json.loads(response)

            # Validate response format
            if not isinstance(errors, list):
                return []

            # Validate each error entry
            validated_errors = []
            for error in errors:
                if not isinstance(error, dict):
                    continue

                # Ensure required fields exist
                if 'category' in error and 'severity' in error:
                    # Normalize severity to 0.0-1.0 range
                    severity = float(error.get('severity', 0.5))
                    error['severity'] = max(0.0, min(1.0, severity))

                    validated_errors.append(error)

            return validated_errors

        except json.JSONDecodeError:
            # LLM didn't return valid JSON - return empty list
            # In production, we'd log this for monitoring
            return []
        except (ValueError, TypeError):
            # Invalid data types in response
            return []
