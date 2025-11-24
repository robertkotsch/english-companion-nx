"""
Ollama LLM client for conversation generation
Handles communication with local Ollama server
"""

import requests
import json
from typing import List, Dict, Optional
from src.core.config import Config


class OllamaClient:
    """Client for Ollama LLM API"""

    def __init__(self, host: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize Ollama client

        Args:
            host: Ollama host (default from config)
            model: Model name (default from config)
        """
        self.host = host or Config.OLLAMA_HOST
        self.model = model or Config.OLLAMA_MODEL
        self.api_url = f"http://{self.host}/api/chat"

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Send chat request to Ollama

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            Generated response text
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }

        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        try:
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=60
            )
            response.raise_for_status()

            data = response.json()
            return data["message"]["content"]

        except requests.exceptions.RequestException as e:
            raise Exception(f"Ollama API request failed: {e}")
        except (KeyError, json.JSONDecodeError) as e:
            raise Exception(f"Invalid Ollama response format: {e}")

    def generate_response(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Generate a response to user message with conversation context

        Args:
            user_message: User's current message
            conversation_history: Previous conversation messages

        Returns:
            Generated response
        """
        messages = conversation_history or []

        # Add user message
        messages.append({
            "role": "user",
            "content": user_message
        })

        # Generate response
        response = self.chat(messages)

        return response

    def test_connection(self) -> bool:
        """
        Test connection to Ollama server

        Returns:
            True if connection successful
        """
        try:
            # Simple test request
            response = self.chat([{"role": "user", "content": "Hello"}])
            return len(response) > 0
        except Exception:
            return False

    def generate(self, prompt: str, model: Optional[str] = None) -> str:
        """
        Generate a response for a single prompt (wrapper for chat)
        
        Args:
            prompt: The input prompt
            model: Optional model override
            
        Returns:
            Generated text
        """
        # Use the instance model if none provided
        # target_model = model or self.model # Unused for now as chat uses self.model
        
        return self.chat([{"role": "user", "content": prompt}])

