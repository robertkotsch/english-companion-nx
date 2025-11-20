"""Data models for Zoo memory agents.

Defines vocabulary items, SRS schedules, session plans, and user profiles.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class VocabStatus(Enum):
    """Vocabulary learning status."""
    NEW = "new"
    LEARNING = "learning"
    REVIEW = "review"
    MASTERED = "mastered"


class VocabType(Enum):
    """Vocabulary item type."""
    WORD = "word"
    PHRASE = "phrase"
    COLLOCATION = "collocation"
    IDIOM = "idiom"


@dataclass
class VocabItem:
    """Vocabulary item from Notion database.
    
    This represents a single entry from the user's Notion vocabulary database.
    Cached locally to minimize API calls and enable offline operation.
    """
    id: str  # Notion page ID
    word: str  # The word/phrase itself
    type: VocabType  # Type of vocabulary item
    definition: str  # Definition or translation
    example: str  # Example sentence
    status: VocabStatus  # Learning status
    category: str  # Category (e.g., "Business", "Academic")
    added_date: str  # ISO format date
    notion_url: str  # Link back to Notion page
    
    # Optional fields
    synonyms: List[str] = field(default_factory=list)
    antonyms: List[str] = field(default_factory=list)
    notes: str = ""
    tags: List[str] = field(default_factory=list)

    @classmethod
    def from_notion_page(cls, page: Dict[str, Any]) -> 'VocabItem':
        """Create VocabItem from Notion API page object.
        
        Args:
            page: Notion page object from API
            
        Returns:
            VocabItem instance
        """
        props = page.get('properties', {})
        
        # Helper to extract property values safely
        def get_text(prop_name: str, default: str = "") -> str:
            prop = props.get(prop_name, {})
            if prop.get('type') == 'title':
                texts = prop.get('title', [])
                return texts[0].get('plain_text', default) if texts else default
            elif prop.get('type') == 'rich_text':
                texts = prop.get('rich_text', [])
                return texts[0].get('plain_text', default) if texts else default
            return default
        
        def get_select(prop_name: str, default: str = "") -> str:
            prop = props.get(prop_name, {})
            select = prop.get('select', {})
            return select.get('name', default) if select else default
        
        def get_multi_select(prop_name: str) -> List[str]:
            prop = props.get(prop_name, {})
            items = prop.get('multi_select', [])
            return [item.get('name', '') for item in items]
        
        def get_date(prop_name: str) -> str:
            prop = props.get(prop_name, {})
            date_obj = prop.get('date', {})
            return date_obj.get('start', '') if date_obj else ''
        
        # Extract fields based on user's specific Notion columns
        # Columns: "Verb Category", "Main Verb + Collocation", "Synonyms (Main Verb)", 
        # "Synonyms (Collocation)", "Relevant Phrasal Verbs", "Positive Adjective", 
        # "Negative Adjective", "Idiomatic Expressions"
        
        # Primary word/phrase is "Main Verb + Collocation"
        word = get_text('Main Verb + Collocation', '')
        
        # Category is the title field "Verb Category"
        category = get_text('Verb Category', 'General')
        
        # Definition/Meaning - construct from synonyms for now as there is no explicit definition column
        synonyms_main = get_text('Synonyms (Main Verb)', '')
        synonyms_collo = get_text('Synonyms (Collocation)', '')
        definition = f"Synonyms: {synonyms_main}"
        if synonyms_collo:
            definition += f"; {synonyms_collo}"
            
        # Construct example/notes from other fields
        phrasal = get_text('Relevant Phrasal Verbs', '')
        idioms = get_text('Idiomatic Expressions', '')
        
        notes_parts = []
        if phrasal: notes_parts.append(f"Phrasal: {phrasal}")
        if idioms: notes_parts.append(f"Idioms: {idioms}")
        notes = " | ".join(notes_parts)
        
        # Adjectives as tags
        pos_adj = get_text('Positive Adjective', '')
        neg_adj = get_text('Negative Adjective', '')
        tags = []
        if pos_adj: tags.append(f"Pos: {pos_adj}")
        if neg_adj: tags.append(f"Neg: {neg_adj}")
        
        # Default values for missing fields
        vocab_type = 'collocation' if ' ' in word else 'word'
        status = 'new' # Default status
        added_date = datetime.now().isoformat() # No added date column visible
        
        return cls(
            id=page['id'],
            word=word,
            type=VocabType(vocab_type) if vocab_type else VocabType.WORD,
            definition=definition,
            example="", # No example column
            status=VocabStatus.NEW,
            category=category,
            added_date=added_date,
            notion_url=page.get('url', ''),
            synonyms=[s.strip() for s in synonyms_main.split(',')] if synonyms_main else [],
            antonyms=[],
            notes=notes,
            tags=tags
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'word': self.word,
            'type': self.type.value,
            'definition': self.definition,
            'example': self.example,
            'status': self.status.value,
            'category': self.category,
            'added_date': self.added_date,
            'notion_url': self.notion_url,
            'synonyms': self.synonyms,
            'antonyms': self.antonyms,
            'notes': self.notes,
            'tags': self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VocabItem':
        """Create VocabItem from dictionary."""
        return cls(
            id=data['id'],
            word=data['word'],
            type=VocabType(data['type']),
            definition=data['definition'],
            example=data['example'],
            status=VocabStatus(data['status']),
            category=data['category'],
            added_date=data['added_date'],
            notion_url=data['notion_url'],
            synonyms=data.get('synonyms', []),
            antonyms=data.get('antonyms', []),
            notes=data.get('notes', ''),
            tags=data.get('tags', [])
        )


@dataclass
class VocabCache:
    """Complete vocabulary cache with metadata.
    
    This is the root object stored in data/vocab/notion_cache.json
    """
    items: List[VocabItem]
    last_sync: str  # ISO format timestamp
    notion_db_id: str
    total_items: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'items': [item.to_dict() for item in self.items],
            'last_sync': self.last_sync,
            'notion_db_id': self.notion_db_id,
            'total_items': self.total_items
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VocabCache':
        """Create VocabCache from dictionary."""
        return cls(
            items=[VocabItem.from_dict(item) for item in data['items']],
            last_sync=data['last_sync'],
            notion_db_id=data['notion_db_id'],
            total_items=data['total_items']
        )


@dataclass
class SRSItem:
    """Spaced Repetition System item for vocabulary or grammar patterns."""
    id: str  # Unique identifier
    type: str  # "vocabulary" | "grammar"
    content: str  # The word/phrase or grammar pattern
    interval_days: int  # Current review interval
    next_review: str  # ISO format date
    ease_factor: float  # SM-2 ease factor (default 2.5)
    repetitions: int  # Number of successful reviews
    last_review: Optional[str] = None  # ISO format date
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'type': self.type,
            'content': self.content,
            'interval_days': self.interval_days,
            'next_review': self.next_review,
            'ease_factor': self.ease_factor,
            'repetitions': self.repetitions,
            'last_review': self.last_review
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SRSItem':
        """Create SRSItem from dictionary."""
        return cls(
            id=data['id'],
            type=data['type'],
            content=data['content'],
            interval_days=data['interval_days'],
            next_review=data['next_review'],
            ease_factor=data['ease_factor'],
            repetitions=data['repetitions'],
            last_review=data.get('last_review')
        )


@dataclass
class SessionPlan:
    """Plan for a single conversation session."""
    session_type: str  # "quick" | "full" | "free"
    duration_target_min: int
    focus: str  # "grammar" | "fillers" | "vocab"
    review_items: List[str]  # SRS item IDs due for review
    drill_budget: int  # Max number of drills
    vocab_targets: List[str]  # Vocab item IDs to practice


@dataclass
class DailyPlan:
    """Daily practice plan created at DAY_BOOT."""
    date: str  # ISO format date
    focus: str  # Primary focus for the day
    review_due: List[str]  # SRS item IDs due today
    session_plans: Dict[str, SessionPlan]  # Plans by session type
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'date': self.date,
            'focus': self.focus,
            'review_due': self.review_due,
            'session_plans': {
                key: {
                    'session_type': plan.session_type,
                    'duration_target_min': plan.duration_target_min,
                    'focus': plan.focus,
                    'review_items': plan.review_items,
                    'drill_budget': plan.drill_budget,
                    'vocab_targets': plan.vocab_targets
                }
                for key, plan in self.session_plans.items()
            }
        }


@dataclass
class UserProfile:
    """User profile with learning preferences and goals."""
    cefr_target: str  # "B2" | "C1" | "C2"
    native_language: str
    accent_preference: str  # "American" | "British"
    coach_intensity: str  # "off" | "soft" | "normal"
    weekly_focus: str  # "grammar" | "vocabulary" | "fluency"
    topics: List[str]  # Preferred conversation topics
    availability_start: str  # "09:00"
    availability_end: str  # "17:00"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserProfile':
        """Create UserProfile from dictionary."""
        return cls(
            cefr_target=data.get('cefr_target', 'C1'),
            native_language=data.get('native_language', 'German'),
            accent_preference=data.get('accent_preference', 'American'),
            coach_intensity=data.get('coach_intensity', 'normal'),
            weekly_focus=data.get('weekly_focus', 'business_communication'),
            topics=data.get('topics', []),
            availability_start=data.get('availability', {}).get('start', '09:00'),
            availability_end=data.get('availability', {}).get('end', '17:00')
        )
