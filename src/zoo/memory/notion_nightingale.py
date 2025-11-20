"""NotionNightingale - Notion vocabulary database sync agent.

Syncs vocabulary from Notion database to local JSON cache.
Read-only in MVP - no writes back to Notion.

Follows CLAUDE.md principles:
- Load once at DAY_BOOT (daily sync)
- Keep cache in RAM after loading
- Minimal SSD writes (cache file only)
- Fallback to cached data if Notion unavailable
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Optional
from pathlib import Path

from notion_client import Client
from notion_client.errors import APIResponseError

from src.zoo.memory.models import VocabItem, VocabCache
from src.zoo.zoo_logger import get_zoo_logger


class NotionNightingale:
    """Notion vocabulary sync agent.
    
    Responsibilities:
    - Sync Notion vocab database at DAY_BOOT
    - Cache to local JSON (data/vocab/notion_cache.json)
    - Provide vocab lookup for LexiLynx and other agents
    - Fallback to cached data if Notion unavailable
    
    Follows "load once, run forever" principle:
    - Loaded at service startup
    - Kept in RAM until service restarts
    - Syncs once per day (or on manual trigger)
    """
    
    def __init__(
        self,
        api_key: str,
        database_id: str,
        cache_dir: str = "data/vocab",
        sync_interval_hours: int = 24
    ):
        """Initialize NotionNightingale.
        
        Args:
            api_key: Notion API integration token
            database_id: Notion database ID to sync
            cache_dir: Directory for cache file
            sync_interval_hours: Hours between syncs (default 24)
        """
        self.api_key = api_key
        self.database_id = database_id
        self.cache_dir = Path(cache_dir)
        self.cache_path = self.cache_dir / "notion_cache.json"
        self.sync_interval_hours = sync_interval_hours
        
        # In-memory cache (loaded once, kept in RAM)
        self._cache: Optional[VocabCache] = None
        self._items_by_id: dict = {}  # Quick lookup by notion ID
        self._items_by_word: dict = {}  # Quick lookup by word
        
        # Notion client (lazy init)
        self._client: Optional[Client] = None
        
        # Logging
        self.logger = get_zoo_logger()
        
        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _init_client(self):
        """Initialize Notion client (lazy)."""
        if self._client is None:
            try:
                self._client = Client(auth=self.api_key)
                self.logger.info("NotionNightingale", "Notion client initialized")
            except Exception as e:
                self.logger.error("NotionNightingale", f"Failed to init Notion client: {e}")
                raise
    
    def load_cache(self) -> bool:
        """Load cache from disk into RAM.
        
        Called at startup to load existing cache.
        Falls back to empty cache if file doesn't exist.
        
        Returns:
            True if cache loaded successfully, False otherwise
        """
        if not self.cache_path.exists():
            self.logger.warning(
                "NotionNightingale",
                f"No cache found at {self.cache_path}, starting with empty cache"
            )
            self._cache = VocabCache(
                items=[],
                last_sync="never",
                notion_db_id=self.database_id,
                total_items=0
            )
            return False
        
        try:
            with open(self.cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._cache = VocabCache.from_dict(data)
            
            # Build lookup indices
            self._items_by_id = {item.id: item for item in self._cache.items}
            self._items_by_word = {item.word.lower(): item for item in self._cache.items}
            
            self.logger.info(
                "NotionNightingale",
                f"Loaded {self._cache.total_items} items from cache (last sync: {self._cache.last_sync})"
            )
            return True
            
        except Exception as e:
            self.logger.error("NotionNightingale", f"Failed to load cache: {e}")
            # Start with empty cache on error
            self._cache = VocabCache(
                items=[],
                last_sync="never",
                notion_db_id=self.database_id,
                total_items=0
            )
            return False
    
    def save_cache(self):
        """Save cache from RAM to disk.
        
        Minimal SSD write - only called after successful sync.
        """
        if self._cache is None:
            self.logger.warning("NotionNightingale", "No cache to save")
            return
        
        try:
            with open(self.cache_path, 'w', encoding='utf-8') as f:
                json.dump(self._cache.to_dict(), f, indent=2, ensure_ascii=False)
            
            self.logger.info(
                "NotionNightingale",
                f"Saved {self._cache.total_items} items to cache"
            )
        except Exception as e:
            self.logger.error("NotionNightingale", f"Failed to save cache: {e}")
    
    def should_sync(self) -> bool:
        """Check if sync is needed based on last sync time.
        
        Returns:
            True if sync interval has elapsed or never synced
        """
        if self._cache is None or self._cache.last_sync == "never":
            return True
        
        try:
            last_sync = datetime.fromisoformat(self._cache.last_sync)
            now = datetime.now()
            elapsed = now - last_sync
            
            should = elapsed.total_seconds() / 3600 >= self.sync_interval_hours
            
            if should:
                self.logger.info(
                    "NotionNightingale",
                    f"Sync needed: {elapsed.total_seconds() / 3600:.1f}h since last sync"
                )
            
            return should
            
        except Exception as e:
            self.logger.error("NotionNightingale", f"Error checking sync time: {e}")
            return True  # Sync on error to be safe
    
    def sync_from_notion(self, force: bool = False) -> bool:
        """Sync vocabulary from Notion database.
        
        Fetches all pages from Notion database and updates local cache.
        Called at DAY_BOOT or manually triggered.
        
        Args:
            force: Force sync even if interval not elapsed
            
        Returns:
            True if sync successful, False otherwise
        """
        if not force and not self.should_sync():
            self.logger.info("NotionNightingale", "Sync not needed, using cached data")
            return True
        
        try:
            self._init_client()
            
            self.logger.info(
                "NotionNightingale",
                f"Starting Notion sync for database {self.database_id[:8]}..."
            )
            
            # Query all pages from database
            items = []
            has_more = True
            start_cursor = None
            
            while has_more:
                try:
                    response = self._client.databases.query(
                        database_id=self.database_id,
                        start_cursor=start_cursor,
                        page_size=100  # Max per request
                    )
                    
                    # Parse pages into VocabItems
                    for page in response.get('results', []):
                        try:
                            item = VocabItem.from_notion_page(page)
                            items.append(item)
                        except Exception as e:
                            self.logger.warning(
                                "NotionNightingale",
                                f"Failed to parse page {page.get('id', 'unknown')}: {e}"
                            )
                    
                    has_more = response.get('has_more', False)
                    start_cursor = response.get('next_cursor')
                    
                except APIResponseError as e:
                    self.logger.error(
                        "NotionNightingale",
                        f"Notion API error: {e}"
                    )
                    return False
            
            # Update cache
            self._cache = VocabCache(
                items=items,
                last_sync=datetime.now().isoformat(),
                notion_db_id=self.database_id,
                total_items=len(items)
            )
            
            # Rebuild lookup indices
            self._items_by_id = {item.id: item for item in items}
            self._items_by_word = {item.word.lower(): item for item in items}
            
            # Save to disk
            self.save_cache()
            
            self.logger.info(
                "NotionNightingale",
                f"✅ Synced {len(items)} items from Notion"
            )
            return True
            
        except Exception as e:
            self.logger.error("NotionNightingale", f"Sync failed: {e}")
            return False
    
    def get_item_by_id(self, notion_id: str) -> Optional[VocabItem]:
        """Get vocabulary item by Notion page ID (fast lookup).
        
        Args:
            notion_id: Notion page ID
            
        Returns:
            VocabItem if found, None otherwise
        """
        return self._items_by_id.get(notion_id)
    
    def get_item_by_word(self, word: str) -> Optional[VocabItem]:
        """Get vocabulary item by word (case-insensitive).
        
        Args:
            word: Word or phrase to look up
            
        Returns:
            VocabItem if found, None otherwise
        """
        return self._items_by_word.get(word.lower())
    
    def search_items(self, query: str) -> List[VocabItem]:
        """Search vocabulary items by partial match.
        
        Args:
            query: Search query (case-insensitive)
            
        Returns:
            List of matching VocabItems
        """
        if self._cache is None:
            return []
        
        query_lower = query.lower()
        matches = []
        
        for item in self._cache.items:
            if (query_lower in item.word.lower() or
                query_lower in item.definition.lower() or
                any(query_lower in tag.lower() for tag in item.tags)):
                matches.append(item)
        
        return matches
    
    def get_items_by_category(self, category: str) -> List[VocabItem]:
        """Get all items in a category.
        
        Args:
            category: Category name
            
        Returns:
            List of VocabItems in category
        """
        if self._cache is None:
            return []
        
        return [item for item in self._cache.items if item.category == category]
    
    def get_items_by_status(self, status: str) -> List[VocabItem]:
        """Get all items with a specific status.
        
        Args:
            status: Status ("new", "learning", "review", "mastered")
            
        Returns:
            List of VocabItems with status
        """
        if self._cache is None:
            return []
        
        return [item for item in self._cache.items if item.status.value == status]
    
    def get_all_items(self) -> List[VocabItem]:
        """Get all vocabulary items.
        
        Returns:
            List of all VocabItems
        """
        if self._cache is None:
            return []
        
        return self._cache.items
    
    def get_cache_info(self) -> dict:
        """Get cache metadata.
        
        Returns:
            Dictionary with cache info
        """
        if self._cache is None:
            return {
                'loaded': False,
                'total_items': 0,
                'last_sync': 'never'
            }
        
        return {
            'loaded': True,
            'total_items': self._cache.total_items,
            'last_sync': self._cache.last_sync,
            'notion_db_id': self._cache.notion_db_id
        }
    
    def initialize(self) -> bool:
        """Initialize agent at startup.
        
        Loads cache from disk and syncs from Notion if needed.
        Called once at DAY_BOOT.
        
        Returns:
            True if initialized successfully
        """
        self.logger.info("NotionNightingale", "Initializing...")
        
        # Load existing cache
        self.load_cache()
        
        # Sync if needed (API key required)
        if self.api_key and self.database_id:
            self.sync_from_notion()
        else:
            self.logger.warning(
                "NotionNightingale",
                "No Notion credentials configured, using cached data only"
            )
        
        return self._cache is not None and len(self._cache.items) > 0
