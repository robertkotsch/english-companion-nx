"""
Conversation logger for English Companion NX
Buffers conversations and writes to JSONL file periodically
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from src.core.config import Config


class ConversationLogger:
    """Manages buffered conversation logging to JSONL"""

    def __init__(
        self,
        log_file: Optional[str] = None,
        buffer_interval: Optional[int] = None
    ):
        """
        Initialize conversation logger

        Args:
            log_file: Path to JSONL log file
            buffer_interval: Seconds between flushes (default: 300 = 5 minutes)
        """
        self.log_file = Path(log_file or Config.CONVERSATION_LOG)
        self.buffer_interval = buffer_interval or Config.CONVERSATION_BUFFER_INTERVAL

        # Ensure log directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # Buffer for conversation entries
        self.buffer: List[Dict] = []
        self.last_flush = time.time()

        print(f"📝 Conversation logger initialized: {self.log_file}")
        print(f"   Buffer interval: {self.buffer_interval}s ({self.buffer_interval // 60} minutes)")

    def log_exchange(
        self,
        user_message: str,
        assistant_message: str,
        metadata: Optional[Dict] = None
    ):
        """
        Log a conversation exchange to buffer

        Args:
            user_message: User's message
            assistant_message: Assistant's response
            metadata: Optional metadata (response time, corrections, etc.)
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "user": user_message,
            "assistant": assistant_message,
            "metadata": metadata or {}
        }

        self.buffer.append(entry)

        # Check if it's time to flush
        if time.time() - self.last_flush >= self.buffer_interval:
            self.flush()

    def flush(self):
        """Write buffered entries to disk"""
        if not self.buffer:
            return

        try:
            # Append to JSONL file
            with open(self.log_file, 'a', encoding='utf-8') as f:
                for entry in self.buffer:
                    f.write(json.dumps(entry, ensure_ascii=False) + '\n')

            print(f"💾 Flushed {len(self.buffer)} conversation(s) to log")

            # Clear buffer
            self.buffer = []
            self.last_flush = time.time()

        except Exception as e:
            print(f"⚠️  Failed to flush conversation log: {e}")

    def load_recent(self, count: int = 10) -> List[Dict]:
        """
        Load recent conversations from log

        Args:
            count: Number of recent conversations to load

        Returns:
            List of conversation entries
        """
        if not self.log_file.exists():
            return []

        try:
            conversations = []
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        conversations.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

            # Return last N conversations
            return conversations[-count:] if conversations else []

        except Exception as e:
            print(f"⚠️  Failed to load conversations: {e}")
            return []

    def get_stats(self) -> Dict:
        """Get conversation statistics"""
        if not self.log_file.exists():
            return {
                "total_conversations": 0,
                "buffered": len(self.buffer),
                "log_size_bytes": 0
            }

        try:
            # Count total conversations
            total = 0
            with open(self.log_file, 'r', encoding='utf-8') as f:
                total = sum(1 for _ in f)

            return {
                "total_conversations": total,
                "buffered": len(self.buffer),
                "log_size_bytes": self.log_file.stat().st_size
            }

        except Exception as e:
            print(f"⚠️  Failed to get stats: {e}")
            return {
                "total_conversations": 0,
                "buffered": len(self.buffer),
                "log_size_bytes": 0
            }

    def cleanup(self):
        """Cleanup and flush remaining buffer"""
        self.flush()
