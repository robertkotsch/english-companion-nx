# Infrastructure Comparison: Domain Radar vs English Companion NX

## Quick Summary

| Aspect | Domain Radar NX | English Companion NX |
|--------|-----------------|-------------------|
| **Complexity** | High (data pipeline) | Low (conversational) |
| **Infrastructure** | PostgreSQL + Redis + Qdrant + Prometheus + Grafana | Just Ollama + JSONL file |
| **Daily SSD Writes** | 10-50GB (collection + processing) | 100-200MB (conversations) |
| **Memory Usage** | Variable (phases: 2GB → 5.5GB) | Constant (~11GB for models) |
| **Deployment** | Hybrid (containers + native) | Native Python service |
| **Purpose** | Intelligence gathering & analysis | Real-time conversation |

---

## Domain Radar NX Infrastructure

### Full Stack Required

```
/var/lib/domain-radar-nx/
├── postgres/      # 1GB+ | Multi-domain intelligence data
├── redis/         # 100MB | API caching, rate limiting
├── qdrant/        # 400MB | Vector embeddings for semantic search
├── prometheus/    # 500MB | Metrics collection
└── grafana/       # 200MB | Dashboard visualization
```

### Why Each Component?

**PostgreSQL:**
- Stores 1000s of collected items (Reddit, ArXiv, etc.)
- Complex relational queries
- TimescaleDB for time-series analysis
- Multiple domains with cross-references

**Redis:**
- Cache API responses (reduce external calls)
- Rate limiting for collectors
- Session management
- Temporary data buffers

**Qdrant:**
- Vector embeddings for content
- Semantic similarity search
- Duplicate detection
- Related content discovery

**Prometheus + Grafana:**
- Monitor collection health
- Track processing phases
- SSD write monitoring (critical!)
- Memory usage across phases
- Alert on anomalies

### Runtime Model

**Containerized (Podman):**
- API server
- Collectors (Reddit, ArXiv)
- Notifiers (Telegram)
- All infrastructure services

**Native (systemd):**
- Ollama LLM
- SSD health monitor
- Memory guard
- Visual monitoring (OLED + RGB)

**Why Hybrid?**
- Containers = easy deployment, isolation
- Native = GPU access, performance-critical services

---

## English Companion NX Infrastructure

### Minimal Stack

```
/mnt/nvme/companion/
└── conversations.jsonl    # Simple append-only log
```

### Optional Additions (Phase 4+)

```
/mnt/nvme/companion/
├── conversations.jsonl    # Main log (buffered)
├── conversations.db       # SQLite for queries (optional)
└── backups/              # Periodic backups

/var/lib/english-companion-nx/ (if monitoring needed)
├── prometheus/           # Metrics (optional)
└── grafana/              # Dashboards (optional)
```

### Why So Simple?

**No PostgreSQL needed:**
- Only storing conversations (chronological)
- Simple append-only pattern
- JSONL or SQLite is sufficient
- No complex relationships

**No Redis needed:**
- No API to cache
- No rate limiting required
- Direct conversational flow
- No session management

**No Qdrant needed (initially):**
- No semantic search required
- No content similarity matching
- Maybe add later for "find similar conversations"

**Prometheus/Grafana optional:**
- Nice to have for metrics
- Not essential for core functionality
- Can add if you want analytics

### Runtime Model

**Native Python Service (systemd):**
- Everything runs as one service
- Direct hardware access
- GPU for Whisper/TTS
- Ollama via API (localhost)

**Why Native Only?**
- Simpler deployment (no containers)
- Direct audio hardware access
- No networking overhead
- Easier debugging

---

## Side-by-Side Comparison

### Data Volume

**Domain Radar:**
```
PostgreSQL: 1000s of items/day
Redis: 100s of cache entries
Qdrant: 1000s of vectors
Logs: 100s of MB/day

Total: 10-50GB writes/day
```

**English Companion NX:**
```
Conversations: 10-50/day
JSONL: One line per conversation
Logs: ~10MB/day

Total: 100-200MB writes/day
```

### Deployment Complexity

**Domain Radar:**
```bash
# Start infrastructure
podman run postgres...
podman run redis...
podman run qdrant...
podman run prometheus...
podman run grafana...

# Start native services
systemctl start ollama
systemctl start ssd-monitor
systemctl start memory-guard

# Deploy application
docker build...
docker push ghcr.io/...
ssh jetson "docker pull && restart"
```

**English Companion NX:**
```bash
# Start Ollama (system service)
systemctl start ollama

# Deploy application
git pull
systemctl --user restart english-companion-nx

# That's it!
```

### Memory Profile

**Domain Radar (Phase-based):**
```
Collection Phase:
├── PostgreSQL: 1GB
├── Redis: 100MB
├── Collectors: 500MB
└── Qdrant: 400MB
Total: ~2GB

Analysis Phase:
├── PostgreSQL: 500MB
├── Ollama: 3.5GB
├── Processing: 1GB
└── Qdrant: 400MB
Total: ~5.5GB

NEVER run both phases simultaneously!
```

**English Companion NX (Always-on):**
```
Constant State:
├── System: 3GB
├── Whisper: 2GB
├── Llama 3.1 13B: 8GB
├── Coqui TTS: 0.5GB
├── Application: 1GB
└── Buffers: 0.5GB
Total: ~15GB (constant)

No phases - just runs 24/7
```

---

## When to Use Each Approach

### Use Domain Radar Pattern When:

✅ Processing large amounts of external data
✅ Multiple data sources (APIs, scraping, etc.)
✅ Complex data relationships
✅ Need semantic search
✅ Batch processing workflows
✅ Separate collection/analysis phases
✅ Multiple domains/topics
✅ Heavy monitoring requirements

**Example use cases:**
- Intelligence gathering systems
- Content aggregation platforms
- Research data pipelines
- Multi-source analytics

---

### Use English Companion NX Pattern When:

✅ Simple conversational interface
✅ Direct user interaction
✅ Linear data flow (input → process → output)
✅ Chronological data storage
✅ Real-time processing
✅ Single purpose application
✅ Minimal dependencies

**Example use cases:**
- Chatbots
- Voice assistants
- Interactive tutors
- Conversational agents

---

## Migration Path

### If You Outgrow Simple Storage

**Phase 1-3: JSONL Only**
```python
# conversations.jsonl (buffered writes)
{"timestamp": "...", "user": "...", "assistant": "..."}
```

**Phase 4: Add SQLite**
```python
# Import JSONL → SQLite for queries
import sqlite3
import json

conn = sqlite3.connect('conversations.db')
with open('conversations.jsonl') as f:
    for line in f:
        conv = json.loads(line)
        conn.execute('INSERT INTO conversations VALUES (...)', conv)
```

**Phase 5: Add Vector Search**
```python
# If you want "find similar conversations"
import qdrant_client

qdrant = qdrant_client.QdrantClient(host="localhost")
# Index conversations for semantic search
```

**But honestly?** JSONL is probably sufficient forever for this use case.

---

## Infrastructure Setup Commands

### Domain Radar (Complex)

```bash
# Create all storage directories
sudo mkdir -p /var/lib/domain-radar-nx/{postgres,redis,qdrant,prometheus,grafana}
sudo chown -R $(id -u):$(id -g) /var/lib/domain-radar-nx

# Fix permissions for rootless Podman
podman unshare chown -R 999:999 /var/lib/domain-radar-nx/postgres
podman unshare chown -R 1000:1000 /var/lib/domain-radar-nx/qdrant
# ... etc

# Start all containers
podman run -d --name radar-postgres ...
podman run -d --name radar-redis ...
podman run -d --name radar-qdrant ...
podman run -d --name radar-prometheus ...
podman run -d --name radar-grafana ...

# Configure monitoring
cp config/monitoring/* /var/lib/domain-radar-nx/
# ... etc
```

### English Companion NX (Simple)

```bash
# Create storage directory
mkdir -p /mnt/nvme/companion/{logs,backups}

# Create conversation log (will be created on first write)
touch /mnt/nvme/companion/conversations.jsonl

# Ensure tmpfs exists (usually automatic)
mkdir -p /tmp/companion-audio

# That's it!
```

---

## Cost of Complexity

### Domain Radar Overhead

**Setup time:** 2-3 hours (first time)
**Maintenance:** Weekly checks on all services
**Troubleshooting:** Multiple services to debug
**Resource usage:** ~2-3GB just for infrastructure
**Failure points:** 5+ services that can fail independently

**But:** Required for the use case!

### English Companion NX Simplicity

**Setup time:** 30 minutes
**Maintenance:** Monthly checks on service
**Troubleshooting:** One service to debug
**Resource usage:** ~100MB for Python app
**Failure points:** Just the one service

**Trade-off:** Less functionality, but that's okay!

---

## Key Takeaway

> **Use the right tool for the job.**

Domain Radar's heavy infrastructure is **necessary** for its data processing mission. 

English Companion NX's minimal infrastructure is **sufficient** for its conversational mission.

**Don't over-engineer!** Start simple, add complexity only when you hit actual limitations.

---

## Quick Decision Tree

```
Do you need to process external data sources?
├── YES → Consider Domain Radar pattern
└── NO ↓
    
Do you need semantic search over content?
├── YES → Consider vector DB (Qdrant)
└── NO ↓
    
Do you need complex queries over data?
├── YES → Consider SQL DB (PostgreSQL/SQLite)
└── NO ↓
    
Do you just need to log conversations?
└── YES → JSONL is fine! ✅
```

For English Companion NX: **JSONL is fine!**

---

**Last Updated:** October 27, 2025  
**Recommendation:** Start with JSONL, add complexity only if/when needed.
