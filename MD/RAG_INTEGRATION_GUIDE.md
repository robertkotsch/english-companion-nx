# RAG Integration with Qdrant - English Companion NX

**Retrieval-Augmented Generation for Enhanced Conversations**

---

## 🎯 Overview

Adding RAG (Retrieval-Augmented Generation) with Qdrant allows the English Companion NX to:

✅ **Remember past conversations semantically** (not just chronologically)  
✅ **Find similar topics discussed before** ("we talked about this last week...")  
✅ **Bring up relevant context** from weeks/months ago  
✅ **Build long-term memory** beyond the immediate context window  
✅ **Personalize responses** based on user's interests and history  

---

## 📋 Integration Timeline

### Phase 1-3: Simple Memory (Current Plan)
```
Conversation History:
└── Last 20 exchanges in context window
└── No long-term semantic memory
└── JSONL append-only log
```

### Phase 4: Add Qdrant RAG (Future)
```
Conversation History:
├── Last 20 exchanges (immediate context)
└── Semantic search over ALL past conversations
    └── Qdrant vector database
    └── Find relevant past topics
    └── Augment LLM context with retrieved memories
```

---

## 🏗️ Architecture with RAG

### System Flow with RAG

```
┌─────────────────────────────────────────────────────────┐
│           User speaks: "Tell me about AI"               │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                  Whisper Transcription                   │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│              Query Understanding & Embedding             │
│     (nomic-embed-text: "Tell me about AI")             │
└─────────────────────────────────────────────────────────┘
                         ↓
                    ┌────┴────┐
                    │         │
         ┌──────────▼─┐   ┌──▼──────────┐
         │  Recent     │   │  Qdrant     │
         │  Context    │   │  Search     │
         │  (last 20)  │   │  (semantic) │
         └──────────┬─┘   └──┬──────────┘
                    │         │
                    └────┬────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│              Context Assembly & Ranking                  │
│  • Recent: Last 20 exchanges                            │
│  • Retrieved: 5 relevant past conversations             │
│  • Deduplicated & ranked by relevance                  │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                   LLM Generation                        │
│  System: You're an English teacher...                  │
│  Context: [Recent + Retrieved conversations]           │
│  User: Tell me about AI                                │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                  Response Synthesis                     │
│  "As we discussed last week about machine learning..." │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                  TTS & Playback                         │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│           Background: Index to Qdrant                   │
│  • Embed conversation                                   │
│  • Store in Qdrant (async)                             │
│  • For future retrieval                                │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 Technical Implementation

### Infrastructure Addition

```bash
# Add Qdrant to existing setup
/var/lib/english-companion-nx/
├── conversations.jsonl        # Existing: Append-only log
└── qdrant/                    # New: Vector database
    └── storage/
```

### Qdrant Container (Podman)

```bash
# Start Qdrant (similar to Domain Radar pattern)
podman run -d --name companion-qdrant \
  --restart unless-stopped \
  -p 127.0.0.1:6333:6333 \
  -p 127.0.0.1:6334:6334 \
  -v /var/lib/english-companion-nx/qdrant:/qdrant/storage:U \
  --health-cmd='curl -sSf http://localhost:6333/readyz || exit 1' \
  --health-interval=30s \
  --health-timeout=10s \
  --health-retries=3 \
  docker.io/qdrant/qdrant:v1.7.4
```

**Why Qdrant?**
- ✅ Fast vector similarity search
- ✅ Lightweight (400MB RAM typical)
- ✅ Persistent storage
- ✅ Production-ready
- ✅ ARM64 compatible

---

## 📦 Python Dependencies

### requirements.txt additions

```txt
# RAG dependencies (add in Phase 4)
qdrant-client==1.7.0           # Qdrant Python client
sentence-transformers==2.2.2   # For embeddings (optional, or use Ollama)
```

**Note:** Can use Ollama's `nomic-embed-text` model instead of sentence-transformers to save memory!

---

## 💻 Code Implementation

### 1. Embedding Service

```python
# src/rag/embeddings.py

import ollama
from typing import List
import numpy as np

class EmbeddingService:
    """Generate embeddings using Ollama"""
    
    def __init__(self, model="nomic-embed-text"):
        self.model = model
        self.client = ollama.Client(host="http://127.0.0.1:11434")
        
        # Warmup
        self._warmup()
    
    def _warmup(self):
        """Load model into memory"""
        try:
            self.embed("warmup")
            print(f"✅ Embedding model {self.model} loaded")
        except Exception as e:
            print(f"❌ Failed to load embedding model: {e}")
    
    def embed(self, text: str) -> List[float]:
        """Generate embedding for text"""
        response = self.client.embeddings(
            model=self.model,
            prompt=text
        )
        return response['embedding']
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        return [self.embed(text) for text in texts]
```

### 2. Qdrant Client

```python
# src/rag/vector_store.py

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Optional
import uuid
from datetime import datetime

class ConversationVectorStore:
    """Manage conversation vectors in Qdrant"""
    
    COLLECTION_NAME = "conversations"
    
    def __init__(self, host="127.0.0.1", port=6333):
        self.client = QdrantClient(host=host, port=port)
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Create collection if it doesn't exist"""
        collections = self.client.get_collections().collections
        exists = any(c.name == self.COLLECTION_NAME for c in collections)
        
        if not exists:
            self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=768,  # nomic-embed-text dimension
                    distance=Distance.COSINE
                )
            )
            print(f"✅ Created Qdrant collection: {self.COLLECTION_NAME}")
    
    def add_conversation(
        self,
        conversation_id: str,
        user_message: str,
        assistant_message: str,
        embedding: List[float],
        timestamp: str,
        metadata: Optional[Dict] = None
    ):
        """Add a conversation to the vector store"""
        
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={
                "conversation_id": conversation_id,
                "user_message": user_message,
                "assistant_message": assistant_message,
                "timestamp": timestamp,
                "metadata": metadata or {}
            }
        )
        
        self.client.upsert(
            collection_name=self.COLLECTION_NAME,
            points=[point]
        )
    
    def search_similar(
        self,
        query_embedding: List[float],
        limit: int = 5,
        score_threshold: float = 0.7
    ) -> List[Dict]:
        """Search for similar conversations"""
        
        results = self.client.search(
            collection_name=self.COLLECTION_NAME,
            query_vector=query_embedding,
            limit=limit,
            score_threshold=score_threshold
        )
        
        return [
            {
                "id": hit.id,
                "score": hit.score,
                "user_message": hit.payload["user_message"],
                "assistant_message": hit.payload["assistant_message"],
                "timestamp": hit.payload["timestamp"],
                "metadata": hit.payload.get("metadata", {})
            }
            for hit in results
        ]
    
    def get_stats(self) -> Dict:
        """Get collection statistics"""
        info = self.client.get_collection(self.COLLECTION_NAME)
        return {
            "total_conversations": info.points_count,
            "vectors_size": info.config.params.vectors.size,
            "distance": info.config.params.vectors.distance
        }
```

### 3. RAG Manager

```python
# src/rag/manager.py

from typing import List, Dict
from .embeddings import EmbeddingService
from .vector_store import ConversationVectorStore
import asyncio
from datetime import datetime

class RAGManager:
    """Coordinate RAG operations"""
    
    def __init__(self):
        self.embeddings = EmbeddingService()
        self.vector_store = ConversationVectorStore()
        self._indexing_queue = []
    
    async def index_conversation(
        self,
        conversation_id: str,
        user_message: str,
        assistant_message: str,
        metadata: Dict = None
    ):
        """Index a conversation (async, non-blocking)"""
        
        # Combine for semantic search
        combined_text = f"User: {user_message}\nAssistant: {assistant_message}"
        
        # Generate embedding (can be slow, run in background)
        embedding = await asyncio.to_thread(
            self.embeddings.embed,
            combined_text
        )
        
        # Store in Qdrant
        self.vector_store.add_conversation(
            conversation_id=conversation_id,
            user_message=user_message,
            assistant_message=assistant_message,
            embedding=embedding,
            timestamp=datetime.now().isoformat(),
            metadata=metadata
        )
    
    async def retrieve_relevant_context(
        self,
        query: str,
        limit: int = 5,
        score_threshold: float = 0.7
    ) -> List[Dict]:
        """Retrieve relevant past conversations"""
        
        # Embed query
        query_embedding = await asyncio.to_thread(
            self.embeddings.embed,
            query
        )
        
        # Search Qdrant
        results = self.vector_store.search_similar(
            query_embedding=query_embedding,
            limit=limit,
            score_threshold=score_threshold
        )
        
        return results
    
    def get_stats(self) -> Dict:
        """Get RAG statistics"""
        return self.vector_store.get_stats()
```

### 4. Conversation Manager (Updated)

```python
# src/conversation/manager.py

from typing import List, Dict
from ..rag.manager import RAGManager
import asyncio

class ConversationManager:
    """Manage conversation flow with RAG"""
    
    def __init__(self, enable_rag: bool = True):
        self.recent_context = []  # Last 20 exchanges
        self.enable_rag = enable_rag
        
        if self.enable_rag:
            self.rag = RAGManager()
    
    async def process_user_input(self, user_message: str) -> str:
        """Process user input with RAG augmentation"""
        
        # 1. Get recent context (always)
        recent = self._get_recent_context(limit=20)
        
        # 2. Get retrieved context (if RAG enabled)
        retrieved = []
        if self.enable_rag:
            retrieved = await self.rag.retrieve_relevant_context(
                query=user_message,
                limit=5,
                score_threshold=0.7
            )
        
        # 3. Assemble context for LLM
        context = self._assemble_context(recent, retrieved)
        
        # 4. Generate response with LLM
        assistant_message = await self._generate_response(
            user_message=user_message,
            context=context
        )
        
        # 5. Update recent context
        self._add_to_recent_context(user_message, assistant_message)
        
        # 6. Index conversation (background, non-blocking)
        if self.enable_rag:
            asyncio.create_task(
                self.rag.index_conversation(
                    conversation_id=self._generate_id(),
                    user_message=user_message,
                    assistant_message=assistant_message
                )
            )
        
        return assistant_message
    
    def _assemble_context(
        self,
        recent: List[Dict],
        retrieved: List[Dict]
    ) -> str:
        """Assemble context from recent + retrieved conversations"""
        
        context_parts = []
        
        # Add retrieved context (if any)
        if retrieved:
            context_parts.append("# Relevant past conversations:")
            for i, conv in enumerate(retrieved, 1):
                context_parts.append(
                    f"\n[Past conversation {i}, similarity: {conv['score']:.2f}]\n"
                    f"User: {conv['user_message']}\n"
                    f"Assistant: {conv['assistant_message']}"
                )
            context_parts.append("\n---\n")
        
        # Add recent context
        context_parts.append("# Recent conversation:")
        for exchange in recent:
            context_parts.append(
                f"User: {exchange['user']}\n"
                f"Assistant: {exchange['assistant']}"
            )
        
        return "\n".join(context_parts)
    
    def _get_recent_context(self, limit: int = 20) -> List[Dict]:
        """Get last N exchanges"""
        return self.recent_context[-limit:]
    
    def _add_to_recent_context(self, user: str, assistant: str):
        """Add exchange to recent context"""
        self.recent_context.append({
            "user": user,
            "assistant": assistant
        })
        
        # Prune if too long
        if len(self.recent_context) > 50:
            self.recent_context = self.recent_context[-50:]
    
    async def _generate_response(
        self,
        user_message: str,
        context: str
    ) -> str:
        """Generate response using LLM"""
        # Implementation depends on your LLM client
        pass
    
    def _generate_id(self) -> str:
        """Generate conversation ID"""
        from uuid import uuid4
        return str(uuid4())
```

---

## 🎯 Use Cases

### 1. Remember Past Topics

**Without RAG:**
```
User: "Tell me about neural networks"
Assistant: [Explains neural networks from scratch]

[2 weeks later]
User: "Can you explain neural networks again?"
Assistant: [Explains from scratch again, no memory of first time]
```

**With RAG:**
```
User: "Tell me about neural networks"
Assistant: [Explains neural networks]

[2 weeks later]
User: "Can you explain neural networks again?"
Assistant: "Of course! We actually discussed this two weeks ago. 
You were particularly interested in backpropagation. Would you 
like me to review that, or focus on a different aspect this time?"
```

### 2. Build on Previous Conversations

**Without RAG:**
```
User: "I want to improve my vocabulary"
Assistant: [Generic vocabulary tips]
```

**With RAG:**
```
User: "I want to improve my vocabulary"
Assistant: "Great! I remember we've discussed words related to 
technology and business in the past. Would you like to continue 
expanding in those areas, or explore new topics?"
```

### 3. Personalized Learning

**Without RAG:**
```
User: "Give me a practice sentence"
Assistant: [Random sentence]
```

**With RAG:**
```
User: "Give me a practice sentence"
Assistant: "Based on our conversations, you're interested in AI 
and startups. How about: 'The startup's innovative AI algorithm 
disrupted the traditional market dynamics.' Let's practice 
pronunciation!"
```

---

## 📊 Resource Impact

### Memory Addition

```
Component                Memory
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Existing:               ~15 GB
Qdrant:                 +400 MB
Embedding model:        +0 MB (use Ollama's nomic-embed-text)
RAG Manager:            +100 MB
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total:                  ~15.5 GB

Still under 16GB limit! ✅
```

### SSD Impact

```
Daily writes:           Typical
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Conversations:          100 MB
Qdrant indexing:        +50 MB (embeddings + vectors)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total:                  ~150 MB/day

Still well under limit! ✅
```

### Performance Impact

```
Without RAG:
└── Response time: ~2-3 seconds

With RAG:
├── Embedding query: +200ms
├── Qdrant search: +100ms
├── Background indexing: 0ms (async)
└── Response time: ~2.3-3.3 seconds

Impact: +300ms (acceptable!) ✅
```

---

## 🔧 Configuration

### .env additions

```bash
# RAG Configuration (add in Phase 4)
ENABLE_RAG=true
QDRANT_HOST=127.0.0.1
QDRANT_PORT=6333
QDRANT_COLLECTION=conversations

# Embedding model (use Ollama)
EMBEDDING_MODEL=nomic-embed-text

# RAG retrieval settings
RAG_RETRIEVAL_LIMIT=5
RAG_SCORE_THRESHOLD=0.7

# Background indexing
RAG_INDEX_ASYNC=true
RAG_INDEX_BATCH_SIZE=10
```

---

## 🚀 Migration Path

### Phase 1-3: Simple Memory (Current)
```python
# Just chronological context
recent_context = get_last_n_exchanges(20)
```

### Phase 4: Add RAG (Future)
```python
# Hybrid: Recent + Retrieved
recent_context = get_last_n_exchanges(20)
retrieved_context = rag.search_similar(query, limit=5)
combined_context = merge(recent_context, retrieved_context)
```

### Backward Compatibility

```python
# Graceful degradation
class ConversationManager:
    def __init__(self, enable_rag: bool = False):
        self.enable_rag = enable_rag
        if enable_rag:
            self.rag = RAGManager()
    
    async def process(self, message: str):
        if self.enable_rag:
            # Use RAG
            return await self._process_with_rag(message)
        else:
            # Simple context
            return await self._process_simple(message)
```

**Start with `enable_rag=False`, enable when ready!**

---

## 🧪 Testing RAG

### 1. Basic Functionality

```python
# test_rag.py

import asyncio
from src.rag.manager import RAGManager

async def test_rag():
    rag = RAGManager()
    
    # Index test conversations
    await rag.index_conversation(
        conversation_id="test-1",
        user_message="What is machine learning?",
        assistant_message="Machine learning is a subset of AI..."
    )
    
    await rag.index_conversation(
        conversation_id="test-2",
        user_message="Tell me about neural networks",
        assistant_message="Neural networks are inspired by the brain..."
    )
    
    # Test retrieval
    results = await rag.retrieve_relevant_context(
        query="Explain AI to me",
        limit=3
    )
    
    print(f"Found {len(results)} relevant conversations:")
    for r in results:
        print(f"  Score: {r['score']:.2f}")
        print(f"  User: {r['user_message']}")
        print(f"  Assistant: {r['assistant_message'][:50]}...")
    
    # Stats
    stats = rag.get_stats()
    print(f"\nStats: {stats}")

if __name__ == "__main__":
    asyncio.run(test_rag())
```

### 2. Performance Testing

```python
# test_rag_performance.py

import asyncio
import time
from src.rag.manager import RAGManager

async def test_performance():
    rag = RAGManager()
    
    # Test query time
    start = time.time()
    results = await rag.retrieve_relevant_context(
        query="Tell me about programming",
        limit=5
    )
    query_time = time.time() - start
    
    print(f"Query time: {query_time*1000:.0f}ms")
    print(f"Results: {len(results)}")
    
    # Test indexing time
    start = time.time()
    await rag.index_conversation(
        conversation_id="perf-test",
        user_message="Test message",
        assistant_message="Test response"
    )
    index_time = time.time() - start
    
    print(f"Index time: {index_time*1000:.0f}ms")

if __name__ == "__main__":
    asyncio.run(test_performance())
```

---

## 📚 Best Practices

### 1. Background Indexing

```python
# DON'T block response
await self.rag.index_conversation(...)  # Blocks user!

# DO index in background
asyncio.create_task(
    self.rag.index_conversation(...)
)  # Non-blocking ✅
```

### 2. Deduplication

```python
def _deduplicate_context(self, recent, retrieved):
    """Remove retrieved items already in recent context"""
    recent_ids = {conv['id'] for conv in recent}
    return [r for r in retrieved if r['id'] not in recent_ids]
```

### 3. Score Threshold

```python
# Too low = irrelevant results
score_threshold = 0.5  # ❌

# Too high = miss relevant results
score_threshold = 0.95  # ❌

# Sweet spot
score_threshold = 0.7  # ✅
```

### 4. Limit Retrieved Context

```python
# Too many = context overflow
limit = 20  # ❌

# Too few = miss important context
limit = 1  # ❌

# Sweet spot
limit = 5  # ✅ (5 retrieved + 20 recent = 25 total)
```

---

## 🎓 Advanced Features (Phase 5+)

### 1. Temporal Decay

```python
# Weight recent conversations higher
def _apply_temporal_decay(self, results):
    for r in results:
        age_days = (now - r['timestamp']).days
        decay = 1 / (1 + 0.1 * age_days)  # Decay over time
        r['score'] *= decay
    return sorted(results, key=lambda x: x['score'], reverse=True)
```

### 2. Topic Clustering

```python
# Group conversations by topic
topics = rag.cluster_conversations(n_clusters=10)
# "Show me all conversations about grammar"
```

### 3. Conversation Summarization

```python
# Summarize long conversation threads
summary = rag.summarize_thread(conversation_ids)
# Use summary instead of full text
```

---

## 🔍 Monitoring

### Qdrant Health

```bash
# Check collection
curl http://127.0.0.1:6333/collections/conversations

# Check stats
curl http://127.0.0.1:6333/collections/conversations
```

### Performance Metrics

```python
# Add to Prometheus metrics
rag_query_duration_seconds = Histogram(...)
rag_indexing_duration_seconds = Histogram(...)
rag_retrieval_results_count = Gauge(...)
```

---

## ✅ Integration Checklist

### Setup
- [ ] Install Qdrant container
- [ ] Pull nomic-embed-text model (`ollama pull nomic-embed-text`)
- [ ] Add qdrant-client to requirements.txt
- [ ] Create RAG module structure

### Development
- [ ] Implement EmbeddingService
- [ ] Implement VectorStore
- [ ] Implement RAGManager
- [ ] Update ConversationManager
- [ ] Add RAG tests

### Configuration
- [ ] Add RAG settings to .env
- [ ] Configure score threshold
- [ ] Set retrieval limit
- [ ] Enable async indexing

### Testing
- [ ] Test basic retrieval
- [ ] Test performance
- [ ] Test with real conversations
- [ ] Verify memory/SSD impact

### Deployment
- [ ] Start Qdrant container
- [ ] Enable RAG in config
- [ ] Monitor performance
- [ ] Collect user feedback

---

## 🎯 Success Metrics

**RAG is working well when:**
- ✅ Retrieves relevant conversations (score > 0.7)
- ✅ Query time < 300ms
- ✅ Background indexing doesn't block responses
- ✅ Memory stays under 16GB
- ✅ SSD writes stay under 500MB/day
- ✅ User notices improved "memory"

---

## 📝 Summary

**RAG with Qdrant adds:**
- ✅ Long-term semantic memory
- ✅ Personalized responses
- ✅ Topic continuity across sessions
- ✅ Better learning experience

**Resource impact:**
- +400MB RAM (Qdrant)
- +50MB/day SSD writes
- +300ms response time
- Still within all limits! ✅

**Perfect for Phase 4-5 enhancement!** 🚀

---

**Last Updated:** October 27, 2025  
**Status:** Future feature (Phase 4-5)  
**Compatibility:** Fits perfectly within Jetson Orin NX 16GB constraints
