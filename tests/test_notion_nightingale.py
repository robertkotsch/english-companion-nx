"""Unit tests for NotionNightingale agent.

Tests vocabulary sync, caching, and lookup functionality.
"""

import json
import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from src.zoo.memory.notion_nightingale import NotionNightingale
from src.zoo.memory.models import VocabItem, VocabCache, VocabType, VocabStatus


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Create temporary cache directory."""
    cache_dir = tmp_path / "vocab"
    cache_dir.mkdir()
    return str(cache_dir)


@pytest.fixture
def mock_vocab_items():
    """Create mock vocabulary items."""
    return [
        VocabItem(
            id="page1",
            word="leverage",
            type=VocabType.WORD,
            definition="use strategically",
            example="We can leverage our expertise",
            status=VocabStatus.LEARNING,
            category="Business",
            added_date="2024-01-01",
            notion_url="https://notion.so/page1"
        ),
        VocabItem(
            id="page2",
            word="facilitate",
            type=VocabType.WORD,
            definition="make easier",
            example="This will facilitate communication",
            status=VocabStatus.REVIEW,
            category="Business",
            added_date="2024-01-02",
            notion_url="https://notion.so/page2"
        )
    ]


@pytest.fixture
def mock_cache(mock_vocab_items):
    """Create mock vocab cache."""
    return VocabCache(
        items=mock_vocab_items,
        last_sync=datetime.now().isoformat(),
        notion_db_id="test_db",
        total_items=len(mock_vocab_items)
    )


class TestNotionNightingale:
    """Test NotionNightingale agent."""
    
    def test_init(self, temp_cache_dir):
        """Test initialization."""
        agent = NotionNightingale(
            api_key="test_key",
            database_id="test_db",
            cache_dir=temp_cache_dir
        )
        
        assert agent.api_key == "test_key"
        assert agent.database_id == "test_db"
        assert agent._cache is None
        assert agent._client is None
    
    def test_load_cache_missing(self, temp_cache_dir):
        """Test loading cache when file doesn't exist."""
        agent = NotionNightingale(
            api_key="test_key",
            database_id="test_db",
            cache_dir=temp_cache_dir
        )
        
        result = agent.load_cache()
        
        assert result is False
        assert agent._cache is not None
        assert agent._cache.total_items == 0
        assert agent._cache.last_sync == "never"
    
    def test_load_cache_success(self, temp_cache_dir, mock_cache):
        """Test loading cache successfully."""
        # Write cache file
        cache_path = Path(temp_cache_dir) / "notion_cache.json"
        with open(cache_path, 'w') as f:
            json.dump(mock_cache.to_dict(), f)
        
        agent = NotionNightingale(
            api_key="test_key",
            database_id="test_db",
            cache_dir=temp_cache_dir
        )
        
        result = agent.load_cache()
        
        assert result is True
        assert agent._cache.total_items == 2
        assert len(agent._items_by_id) == 2
        assert len(agent._items_by_word) == 2
    
    def test_save_cache(self, temp_cache_dir, mock_cache):
        """Test saving cache to disk."""
        agent = NotionNightingale(
            api_key="test_key",
            database_id="test_db",
            cache_dir=temp_cache_dir
        )
        agent._cache = mock_cache
        
        agent.save_cache()
        
        # Verify file exists and content is correct
        cache_path = Path(temp_cache_dir) / "notion_cache.json"
        assert cache_path.exists()
        
        with open(cache_path, 'r') as f:
            data = json.load(f)
        
        assert data['total_items'] == 2
        assert len(data['items']) == 2
    
    def test_should_sync_never_synced(self, temp_cache_dir):
        """Test should_sync when never synced."""
        agent = NotionNightingale(
            api_key="test_key",
            database_id="test_db",
            cache_dir=temp_cache_dir
        )
        agent.load_cache()  # Creates empty cache with last_sync="never"
        
        assert agent.should_sync() is True
    
    def test_should_sync_interval_elapsed(self, temp_cache_dir, mock_vocab_items):
        """Test should_sync when interval has elapsed."""
        # Create cache with old sync time
        old_sync = "2024-01-01T00:00:00"
        cache = VocabCache(
            items=mock_vocab_items,
            last_sync=old_sync,
            notion_db_id="test_db",
            total_items=2
        )
        
        agent = NotionNightingale(
            api_key="test_key",
            database_id="test_db",
            cache_dir=temp_cache_dir,
            sync_interval_hours=1  # Short interval for testing
        )
        agent._cache = cache
        
        assert agent.should_sync() is True
    
    def test_get_item_by_id(self, temp_cache_dir, mock_cache):
        """Test getting item by Notion ID."""
        agent = NotionNightingale(
            api_key="test_key",
            database_id="test_db",
            cache_dir=temp_cache_dir
        )
        agent._cache = mock_cache
        agent._items_by_id = {item.id: item for item in mock_cache.items}
        
        item = agent.get_item_by_id("page1")
        
        assert item is not None
        assert item.word == "leverage"
    
    def test_get_item_by_word(self, temp_cache_dir, mock_cache):
        """Test getting item by word (case-insensitive)."""
        agent = NotionNightingale(
            api_key="test_key",
            database_id="test_db",
            cache_dir=temp_cache_dir
        )
        agent._cache = mock_cache
        agent._items_by_word = {item.word.lower(): item for item in mock_cache.items}
        
        # Test case-insensitive lookup
        item = agent.get_item_by_word("LEVERAGE")
        
        assert item is not None
        assert item.word == "leverage"
    
    def test_search_items(self, temp_cache_dir, mock_cache):
        """Test searching items by partial match."""
        agent = NotionNightingale(
            api_key="test_key",
            database_id="test_db",
            cache_dir=temp_cache_dir
        )
        agent._cache = mock_cache
        
        # Search by word partial match
        results = agent.search_items("lev")
        assert len(results) == 1
        assert results[0].word == "leverage"
        
        # Search by definition
        results = agent.search_items("easier")
        assert len(results) == 1
        assert results[0].word == "facilitate"
    
    def test_get_items_by_category(self, temp_cache_dir, mock_cache):
        """Test getting items by category."""
        agent = NotionNightingale(
            api_key="test_key",
            database_id="test_db",
            cache_dir=temp_cache_dir
        )
        agent._cache = mock_cache
        
        results = agent.get_items_by_category("Business")
        assert len(results) == 2
    
    def test_get_items_by_status(self, temp_cache_dir, mock_cache):
        """Test getting items by status."""
        agent = NotionNightingale(
            api_key="test_key",
            database_id="test_db",
            cache_dir=temp_cache_dir
        )
        agent._cache = mock_cache
        
        results = agent.get_items_by_status("learning")
        assert len(results) == 1
        assert results[0].word == "leverage"
    
    def test_get_cache_info(self, temp_cache_dir, mock_cache):
        """Test getting cache metadata."""
        agent = NotionNightingale(
            api_key="test_key",
            database_id="test_db",
            cache_dir=temp_cache_dir
        )
        agent._cache = mock_cache
        
        info = agent.get_cache_info()
        
        assert info['loaded'] is True
        assert info['total_items'] == 2
        assert info['notion_db_id'] == "test_db"
    
    def test_initialize_no_credentials(self, temp_cache_dir):
        """Test initialization without Notion credentials."""
        agent = NotionNightingale(
            api_key="",
            database_id="",
            cache_dir=temp_cache_dir
        )
        
        # Should load cache but not sync
        result = agent.initialize()
        
        assert agent._cache is not None
        # Will be False since no cache file exists and no sync happened
        assert result is False
    
    @patch('src.zoo.memory.notion_nightingale.Client')
    def test_sync_from_notion_success(self, mock_client_class, temp_cache_dir):
        """Test successful Notion sync."""
        # Mock Notion API response
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_response = {
            'results': [
                {
                    'id': 'page1',
                    'url': 'https://notion.so/page1',
                    'properties': {
                        'Name': {
                            'type': 'title',
                            'title': [{'plain_text': 'leverage'}]
                        },
                        'Type': {
                            'type': 'select',
                            'select': {'name': 'word'}
                        },
                        'Definition': {
                            'type': 'rich_text',
                            'rich_text': [{'plain_text': 'use strategically'}]
                        },
                        'Example': {
                            'type': 'rich_text',
                            'rich_text': [{'plain_text': 'We can leverage'}]
                        },
                        'Status': {
                            'type': 'select',
                            'select': {'name': 'learning'}
                        },
                        'Category': {
                            'type': 'select',
                            'select': {'name': 'Business'}
                        },
                        'Added': {
                            'type': 'date',
                            'date': {'start': '2024-01-01'}
                        }
                    }
                }
            ],
            'has_more': False
        }
        
        mock_client.databases.query.return_value = mock_response
        
        agent = NotionNightingale(
            api_key="test_key",
            database_id="test_db",
            cache_dir=temp_cache_dir
        )
        agent.load_cache()
        
        result = agent.sync_from_notion(force=True)
        
        assert result is True
        assert agent._cache.total_items == 1
        assert agent._items_by_word['leverage'] is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
