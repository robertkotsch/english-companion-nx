import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.zoo.memory.notion_nightingale import NotionNightingale
from src.zoo.zoo_logger import get_zoo_logger, set_zoo_log_level

def test_sync():
    # Load environment variables
    load_dotenv()
    
    api_key = os.getenv("NOTION_API_KEY")
    db_id = os.getenv("NOTION_VOCAB_DB_ID")
    
    print(f"DEBUG: API Key found: {'Yes' if api_key else 'No'}")
    print(f"DEBUG: DB ID found: {'Yes' if db_id else 'No'}")
    
    if not api_key or not db_id:
        print("❌ Missing credentials in .env")
        print("Please ensure NOTION_API_KEY and NOTION_VOCAB_DB_ID are set in .env")
        return

    # Setup logging
    set_zoo_log_level(logging.DEBUG)
    
    # Initialize agent
    print("\nInitializing NotionNightingale...")
    agent = NotionNightingale(
        api_key=api_key,
        database_id=db_id,
        cache_dir="data/vocab"
    )
    
    # Force sync
    print("\nStarting sync...")
    success = agent.sync_from_notion(force=True)
    
    if success:
        print("\n✅ Sync successful!")
        info = agent.get_cache_info()
        print(f"Items synced: {info['total_items']}")
        
        # Show first few items
        items = agent.get_all_items()
        if items:
            print("\nSample items:")
            for item in items[:3]:
                print(f"- {item.word} ({item.type}): {item.definition}")
    else:
        print("\n❌ Sync failed. Check logs for details.")

if __name__ == "__main__":
    test_sync()
