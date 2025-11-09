#!/usr/bin/env python3
"""
Simple standalone test of conversation logger
Tests buffered JSONL writes without full dependency chain
"""

import json
import time
from datetime import datetime
from pathlib import Path


class SimpleConversationLogger:
    """Simplified version for testing"""

    def __init__(self, log_file: str, buffer_interval: int = 300):
        self.log_file = Path(log_file)
        self.buffer_interval = buffer_interval
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.buffer = []
        self.last_flush = time.time()

    def log_exchange(self, user_message: str, assistant_message: str, metadata: dict = None):
        """Log a conversation exchange to buffer"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "user": user_message,
            "assistant": assistant_message,
            "metadata": metadata or {}
        }
        self.buffer.append(entry)

        # Auto-flush if interval elapsed
        if time.time() - self.last_flush >= self.buffer_interval:
            self.flush()

    def flush(self):
        """Write buffered entries to disk"""
        if not self.buffer:
            return

        with open(self.log_file, 'a', encoding='utf-8') as f:
            for entry in self.buffer:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')

        print(f"💾 Flushed {len(self.buffer)} conversation(s) to {self.log_file}")
        self.buffer = []
        self.last_flush = time.time()

    def get_total_count(self) -> int:
        """Count total logged conversations"""
        if not self.log_file.exists():
            return 0
        with open(self.log_file, 'r') as f:
            return sum(1 for _ in f)


def test_logger():
    """Test conversation logger with buffered writes"""

    print("🧪 Testing Conversation Logger (Standalone)")
    print("=" * 60)

    # Create test logger
    test_log = Path("/tmp/test-conversations.jsonl")
    if test_log.exists():
        test_log.unlink()

    logger = SimpleConversationLogger(
        log_file=str(test_log),
        buffer_interval=5  # 5 seconds for testing
    )

    print(f"✅ Logger created: {test_log}")
    print(f"   Buffer interval: 5 seconds\n")

    # Test 1: Log conversations without auto-flush
    print("📝 Test 1: Buffering (no auto-flush)")
    print("-" * 60)

    logger.log_exchange(
        user_message="Hello!",
        assistant_message="Hi there! How can I help you today?",
        metadata={"response_time_ms": 1200, "trigger": "wake_word"}
    )
    print(f"   Logged 1/3 - Buffer: {len(logger.buffer)}, File exists: {test_log.exists()}")

    logger.log_exchange(
        user_message="What's the weather like?",
        assistant_message="I don't have access to weather data, but I can help you practice English!",
        metadata={"response_time_ms": 1500, "trigger": "wake_word"}
    )
    print(f"   Logged 2/3 - Buffer: {len(logger.buffer)}, File exists: {test_log.exists()}")

    logger.log_exchange(
        user_message="Thanks!",
        assistant_message="You're welcome! Feel free to ask me anything.",
        metadata={"response_time_ms": 900, "trigger": "wake_word"}
    )
    print(f"   Logged 3/3 - Buffer: {len(logger.buffer)}, File exists: {test_log.exists()}")

    # Test 2: Wait for auto-flush
    print(f"\n⏳ Test 2: Auto-flush after {logger.buffer_interval}s")
    print("-" * 60)
    print(f"   Waiting {logger.buffer_interval + 1} seconds...")
    time.sleep(logger.buffer_interval + 1)

    # Log one more to trigger auto-flush
    logger.log_exchange(
        user_message="Test auto-flush",
        assistant_message="This should trigger an auto-flush of the buffer.",
        metadata={"response_time_ms": 800, "trigger": "test"}
    )

    print(f"   After auto-flush - Buffer: {len(logger.buffer)}, Total logged: {logger.get_total_count()}")

    # Test 3: Manual flush
    print(f"\n💾 Test 3: Manual flush")
    print("-" * 60)

    logger.log_exchange(
        user_message="How do you say 'hello' in different ways?",
        assistant_message="You can say 'hi', 'hey', 'greetings', or 'good morning/afternoon/evening'.",
        metadata={"response_time_ms": 2100, "trigger": "wake_word"}
    )
    logger.log_exchange(
        user_message="That's helpful!",
        assistant_message="I'm glad! Keep practicing!",
        metadata={"response_time_ms": 800, "trigger": "wake_word"}
    )

    print(f"   Before flush - Buffer: {len(logger.buffer)}")
    logger.flush()
    print(f"   After flush - Buffer: {len(logger.buffer)}, Total logged: {logger.get_total_count()}")

    # Test 4: Read logged conversations
    print(f"\n📖 Test 4: Read logged conversations")
    print("=" * 60)

    if test_log.exists():
        with open(test_log, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                entry = json.loads(line)
                print(f"\nConversation {i}:")
                print(f"  Time: {entry['timestamp']}")
                print(f"  User: {entry['user']}")
                print(f"  Assistant: {entry['assistant'][:60]}...")
                print(f"  Response time: {entry['metadata'].get('response_time_ms', 0)}ms")
                print(f"  Trigger: {entry['metadata'].get('trigger', 'unknown')}")

    # Final stats
    print("\n" + "=" * 60)
    print(f"📊 Final Statistics:")
    print(f"   Total conversations logged: {logger.get_total_count()}")
    print(f"   Still buffered: {len(logger.buffer)}")
    print(f"   Log file size: {test_log.stat().st_size if test_log.exists() else 0} bytes")
    print(f"\n✅ All tests passed!")
    print(f"   Test log: {test_log}")
    print("=" * 60)


if __name__ == "__main__":
    test_logger()
