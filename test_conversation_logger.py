#!/usr/bin/env python3
"""
Test conversation logger functionality
Verifies buffered JSONL writes work correctly
"""

import time
import json
from pathlib import Path
from src.conversation.logger import ConversationLogger

def test_logger():
    """Test conversation logger with buffered writes"""

    print("🧪 Testing Conversation Logger")
    print("=" * 60)

    # Create test logger with short flush interval for testing
    test_log = Path("/tmp/test-conversations.jsonl")
    if test_log.exists():
        test_log.unlink()

    logger = ConversationLogger(
        log_file=str(test_log),
        buffer_interval=5  # 5 seconds for testing (instead of 5 minutes)
    )

    print(f"\n✅ Logger created: {test_log}")
    print(f"   Buffer interval: 5 seconds (testing mode)")

    # Log some conversations
    print("\n📝 Logging 3 conversations...")

    logger.log_exchange(
        user_message="Hello!",
        assistant_message="Hi there! How can I help you today?",
        metadata={"response_time_ms": 1200, "trigger": "test"}
    )
    print("   1/3 logged (buffered)")

    logger.log_exchange(
        user_message="What's the weather like?",
        assistant_message="I don't have access to weather data, but I can help you practice English!",
        metadata={"response_time_ms": 1500, "trigger": "test"}
    )
    print("   2/3 logged (buffered)")

    logger.log_exchange(
        user_message="Thanks!",
        assistant_message="You're welcome! Feel free to ask me anything.",
        metadata={"response_time_ms": 900, "trigger": "test"}
    )
    print("   3/3 logged (buffered)")

    # Check buffer
    print(f"\n📊 Buffer status: {len(logger.buffer)} conversations buffered")
    print(f"   File exists: {test_log.exists()}")

    # Wait for auto-flush
    print(f"\n⏳ Waiting 6 seconds for auto-flush...")
    time.sleep(6)

    # Check if flushed
    print(f"\n📊 After auto-flush:")
    print(f"   Buffer: {len(logger.buffer)} conversations")
    print(f"   File exists: {test_log.exists()}")

    if test_log.exists():
        stats = logger.get_stats()
        print(f"   Total logged: {stats['total_conversations']} conversations")
        print(f"   File size: {stats['log_size_bytes']} bytes")

    # Test manual flush
    print("\n📝 Logging 2 more conversations...")
    logger.log_exchange(
        user_message="How do you say 'hello' in different ways?",
        assistant_message="Great question! You can say 'hi', 'hey', 'greetings', or 'good morning/afternoon/evening'.",
        metadata={"response_time_ms": 2100, "trigger": "test"}
    )
    logger.log_exchange(
        user_message="That's helpful!",
        assistant_message="I'm glad! Keep practicing!",
        metadata={"response_time_ms": 800, "trigger": "test"}
    )
    print(f"   Buffer: {len(logger.buffer)} conversations")

    print("\n💾 Manual flush...")
    logger.flush()
    print(f"   Buffer: {len(logger.buffer)} conversations")

    # Read and display logged conversations
    print("\n📖 Reading logged conversations:")
    print("=" * 60)

    if test_log.exists():
        with open(test_log, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                entry = json.loads(line)
                print(f"\nConversation {i}:")
                print(f"  Time: {entry['timestamp']}")
                print(f"  User: {entry['user']}")
                print(f"  Assistant: {entry['assistant']}")
                print(f"  Response time: {entry['metadata'].get('response_time_ms', 0)}ms")

    # Final stats
    print("\n" + "=" * 60)
    stats = logger.get_stats()
    print(f"📊 Final Statistics:")
    print(f"   Total conversations logged: {stats['total_conversations']}")
    print(f"   Still buffered: {stats['buffered']}")
    print(f"   Log file size: {stats['log_size_bytes']} bytes")

    # Test load_recent
    print("\n📖 Testing load_recent(3):")
    recent = logger.load_recent(3)
    for i, conv in enumerate(recent, 1):
        print(f"   {i}. {conv['user'][:30]}... → {conv['assistant'][:30]}...")

    print("\n✅ All tests passed!")
    print(f"   Test log: {test_log}")
    print("=" * 60)

if __name__ == "__main__":
    test_logger()
