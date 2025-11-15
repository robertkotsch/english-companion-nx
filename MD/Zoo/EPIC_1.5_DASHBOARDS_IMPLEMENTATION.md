# Epic 1.5: Core Dashboards Implementation Plan

**Goal:** Quick, motivating overview of consistency, grammar, fillers, and vocab usage - using only Phase 1 agents.

**Prerequisites:** Epic 1 (MVP) complete and stable, with ScribeSparrow logging operational.

**Timing:** Implement immediately after Epic 1, before starting Epic 2.

---

## 1. Architecture Overview

### Dashboard Architecture
```
[Phase 1 Agents] → [ScribeSparrow Logs] → [Dashboard API] → [Web UI]
                                              ↓
                                         [Data Aggregator]
                                              ↓
                                    [Statistics Calculator]
```

### Technology Stack Decision

**Option A: Web Dashboard (Recommended for Jetson)**
- **Backend:** FastAPI (lightweight Python web framework)
- **Frontend:** Static HTML + Chart.js (no build step, minimal resources)
- **Deployment:** systemd service on port 8080
- **Access:** http://jetson-nx.local:8080
- **Pros:** Visual, responsive, accessible from any device on network
- **Cons:** ~150MB RAM overhead

**Option B: Terminal Dashboard**
- **Framework:** Rich (Python terminal UI)
- **Display:** Terminal-based charts/tables
- **Pros:** Zero web overhead, runs in SSH session
- **Cons:** Less visual, harder to share

**Decision:** Implement both, start with Web (Option A) as primary, Terminal as fallback.

---

## 2. File Structure

```
english-companion-nx/
├── src/
│   ├── dashboards/                      # NEW: Dashboard system
│   │   ├── __init__.py
│   │   ├── api.py                       # FastAPI backend
│   │   ├── aggregator.py                # Data aggregation logic
│   │   ├── statistics.py                # Stats calculation
│   │   │
│   │   ├── routes/                      # API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── consistency.py          # Consistency & Time dashboard
│   │   │   ├── grammar_fillers.py      # Grammar & Fillers dashboard
│   │   │   ├── vocabulary.py           # Vocabulary dashboard
│   │   │   └── session_review.py       # Last session view
│   │   │
│   │   ├── models/                      # Dashboard data models
│   │   │   ├── __init__.py
│   │   │   ├── session_stats.py
│   │   │   ├── grammar_stats.py
│   │   │   └── vocab_stats.py
│   │   │
│   │   └── terminal/                    # Terminal UI (fallback)
│   │       ├── __init__.py
│   │       └── dashboard_terminal.py
│   │
│   └── zoo/
│       └── flow/
│           └── scribe_sparrow.py        # EXTENDED: Enhanced logging
│
├── web/                                 # NEW: Web dashboard frontend
│   ├── index.html                       # Main dashboard page
│   ├── static/
│   │   ├── css/
│   │   │   └── dashboard.css
│   │   ├── js/
│   │   │   ├── charts.js               # Chart.js wrapper
│   │   │   ├── consistency.js          # Dashboard 1 logic
│   │   │   ├── grammar_fillers.js      # Dashboard 2 logic
│   │   │   ├── vocabulary.js           # Dashboard 3 logic
│   │   │   └── session_review.js       # Dashboard 4 logic
│   │   └── vendor/
│   │       └── chart.min.js            # Chart.js library
│   │
│   └── templates/
│       ├── consistency.html
│       ├── grammar_fillers.html
│       ├── vocabulary.html
│       └── session_review.html
│
├── dashboard_server.py                  # NEW: Dashboard server entry point
├── dashboard_cli.py                     # NEW: Terminal dashboard CLI
├── requirements-dashboard.txt           # Dashboard dependencies
└── .env                                 # Add dashboard config
```

---

## 3. Core Components

### 3.1 Data Aggregator (`src/dashboards/aggregator.py`)

**Purpose:** Read ScribeSparrow logs and aggregate data for dashboard queries.

**Data Sources:**
- `data/progress/utterance_logs.jsonl` - Per-utterance logs
- `data/progress/session_summaries/*.json` - Session summaries
- `data/progress/srs_schedule.json` - SRS review data
- `data/vocab/usage_log.jsonl` - Vocab usage events

**Methods:**
```python
class DataAggregator:
    def __init__(self, log_directory: str):
        self.log_dir = log_directory
        self._cache = {}  # LRU cache for expensive queries

    def get_sessions_by_date(self, start_date, end_date) -> List[Session]
    def get_utterances_by_session(self, session_id) -> List[Utterance]
    def get_vocab_usage_by_date(self, start_date, end_date) -> List[VocabEvent]
    def get_daily_stats(self, date) -> DailyStats
    def get_trend_data(self, metric: str, days: int) -> TimeSeriesData
```

**Caching Strategy:**
- Cache daily aggregations (immutable once day complete)
- Invalidate cache for current day on new session
- LRU cache max 30 days worth of data (~5MB)

**Resource:** ~50MB RAM, <100ms query time

---

### 3.2 Statistics Calculator (`src/dashboards/statistics.py`)

**Purpose:** Compute derived metrics from aggregated data.

**Metrics:**

**Consistency Metrics:**
```python
def calculate_session_streak(sessions: List[Session]) -> int
def calculate_speaking_time_per_day(sessions: List[Session]) -> Dict[str, float]
def calculate_session_distribution(sessions: List[Session]) -> Dict[str, int]
```

**Grammar & Filler Metrics:**
```python
def calculate_grammar_error_rate(utterances: List[Utterance]) -> float
def calculate_filler_rate(utterances: List[Utterance]) -> float
def calculate_error_breakdown_by_type(signals: List[Signal]) -> Dict[str, int]
def calculate_fluency_metrics(utterances: List[Utterance]) -> FluencyStats
```

**Vocabulary Metrics:**
```python
def calculate_vocab_seen_vs_used(vocab_events: List[VocabEvent]) -> Tuple[int, int]
def calculate_top_active_vocab(vocab_events: List[VocabEvent], n=10) -> List[VocabItem]
def calculate_sleeping_vocab(vocab_events: List[VocabEvent], days=30) -> List[VocabItem]
def calculate_review_success_rate(srs_events: List[SRSEvent]) -> float
```

---

### 3.3 FastAPI Backend (`src/dashboards/api.py`)

**Endpoints:**

#### Health Check
```
GET /api/health
Response: {"status": "ok", "version": "1.5.0"}
```

#### Dashboard 1: Consistency & Time
```
GET /api/consistency/sessions?days=28
Response: {
  "sessions_per_day": [
    {"date": "2024-12-01", "focused": 2, "free": 1},
    {"date": "2024-12-02", "focused": 1, "free": 0},
    ...
  ],
  "speaking_time_per_day": [
    {"date": "2024-12-01", "minutes": 18.5},
    ...
  ],
  "streak": {
    "current": 5,
    "longest": 12,
    "days_with_sessions": 5,
    "total_days": 7,
    "message": "Solid: 5/7 days with at least one session"
  }
}
```

#### Dashboard 2: Grammar & Fillers
```
GET /api/grammar-fillers/trends?days=28
Response: {
  "grammar_error_rate": [
    {"date": "2024-12-01", "errors_per_100_words": 4.2},
    ...
  ],
  "error_breakdown": {
    "articles": 12,
    "tense": 8,
    "prepositions": 5,
    "word_order": 3
  },
  "filler_rate": [
    {"date": "2024-12-01", "percentage": 8.5},
    ...
  ],
  "fluency": {
    "typical_wpm": "110-130",
    "median_pause_sec": 0.6
  }
}
```

#### Dashboard 3: Vocabulary
```
GET /api/vocabulary/stats?days=7
Response: {
  "active_vs_passive": {
    "seen": 42,
    "used": 18,
    "ratio": "18/42"
  },
  "top_active": [
    {
      "word": "leverage",
      "times_used": 8,
      "last_used": "2024-12-15",
      "category": "Communication Verbs"
    },
    ...
  ],
  "sleeping_items": [
    {
      "word": "facilitate",
      "last_used": "2024-11-10",
      "days_dormant": 35
    },
    ...
  ],
  "review_stats": {
    "items_reviewed_today": 5,
    "items_reviewed_week": 23,
    "success_rate": 0.72,
    "easy_percentage": 72,
    "struggled_percentage": 28
  }
}
```

#### Dashboard 4: Session Review
```
GET /api/session/last
Response: {
  "session_id": "2024-12-15_1430",
  "type": "quick",
  "duration_min": 6.5,
  "focus": "fillers",
  "timeline": [
    {
      "time_range": "0-3 min",
      "activity": "Warm-up",
      "topic": "e-learning project"
    },
    {
      "time_range": "3-6 min",
      "activity": "Grammar focus",
      "topic": "articles",
      "drills": [
        {"type": "grammar", "completed": true}
      ]
    }
  ],
  "drills_summary": {
    "offered": 3,
    "completed": 2,
    "skipped": 1
  },
  "vocab_practiced": ["leverage", "facilitate"],
  "coach_summary": "Today you reduced fillers slightly, and you practised 2 expressions from your Notion list. Next time, we can build on the same topic or switch focus to phrasal verbs."
}
```

---

### 3.4 Web Frontend

#### Main Dashboard Page (`web/index.html`)

**Layout:**
```html
<!DOCTYPE html>
<html>
<head>
    <title>English Companion - Progress Dashboard</title>
    <link rel="stylesheet" href="/static/css/dashboard.css">
    <script src="/static/vendor/chart.min.js"></script>
</head>
<body>
    <nav>
        <h1>English Companion Dashboard</h1>
        <ul>
            <li><a href="#consistency">Consistency</a></li>
            <li><a href="#grammar">Grammar & Fillers</a></li>
            <li><a href="#vocabulary">Vocabulary</a></li>
            <li><a href="#session">Last Session</a></li>
        </ul>
    </nav>

    <main>
        <section id="consistency">
            <!-- Dashboard 1: Loaded via consistency.js -->
        </section>

        <section id="grammar">
            <!-- Dashboard 2: Loaded via grammar_fillers.js -->
        </section>

        <section id="vocabulary">
            <!-- Dashboard 3: Loaded via vocabulary.js -->
        </section>

        <section id="session">
            <!-- Dashboard 4: Loaded via session_review.js -->
        </section>
    </main>

    <script src="/static/js/charts.js"></script>
    <script src="/static/js/consistency.js"></script>
    <script src="/static/js/grammar_fillers.js"></script>
    <script src="/static/js/vocabulary.js"></script>
    <script src="/static/js/session_review.js"></script>
</body>
</html>
```

#### Chart Examples (Chart.js)

**Sessions Per Day (Bar Chart):**
```javascript
// web/static/js/consistency.js
async function loadConsistencyDashboard() {
    const data = await fetch('/api/consistency/sessions?days=28').then(r => r.json());

    const ctx = document.getElementById('sessionsChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.sessions_per_day.map(d => d.date),
            datasets: [
                {
                    label: 'Focused Sessions',
                    data: data.sessions_per_day.map(d => d.focused),
                    backgroundColor: '#2563eb'
                },
                {
                    label: 'Free Conversation',
                    data: data.sessions_per_day.map(d => d.free),
                    backgroundColor: '#93c5fd'
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { stepSize: 1 }
                }
            }
        }
    });
}
```

**Grammar Error Rate (Line Chart):**
```javascript
// web/static/js/grammar_fillers.js
async function loadGrammarTrends() {
    const data = await fetch('/api/grammar-fillers/trends?days=28').then(r => r.json());

    const ctx = document.getElementById('grammarTrendChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.grammar_error_rate.map(d => d.date),
            datasets: [
                {
                    label: 'Errors per 100 words',
                    data: data.grammar_error_rate.map(d => d.errors_per_100_words),
                    borderColor: '#dc2626',
                    tension: 0.3
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}
```

---

### 3.5 Terminal Dashboard (`src/dashboards/terminal/dashboard_terminal.py`)

**Purpose:** Fallback dashboard for SSH sessions or minimal resource mode.

**Framework:** Rich (Python terminal UI library)

**Example Output:**
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  English Companion - Progress Dashboard           ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

📊 Consistency & Time (Last 7 days)
┌────────────┬──────────┬──────────────┐
│ Date       │ Sessions │ Speaking Min │
├────────────┼──────────┼──────────────┤
│ 2024-12-09 │ 2        │ 15.5         │
│ 2024-12-10 │ 1        │ 8.0          │
│ 2024-12-11 │ 0        │ 0.0          │
│ 2024-12-12 │ 3        │ 22.0         │
│ 2024-12-13 │ 1        │ 6.5          │
│ 2024-12-14 │ 2        │ 14.0         │
│ 2024-12-15 │ 1        │ 7.0          │
└────────────┴──────────┴──────────────┘

🔥 Streak: 5/7 days with sessions

📝 Grammar & Fillers (This week)
• Grammar errors: 3.2 per 100 words (↓ from 4.1 last week)
• Filler rate: 7.8% (↓ from 9.2%)
• Most common error: articles (12 instances)

📚 Vocabulary
• Seen: 42 | Used: 18 (ratio: 43%)
• Top active: leverage (8×), facilitate (5×), framework (4×)
• Sleeping: 15 items not used in 30+ days

⏱️  Last Session (2024-12-15 14:30)
• Duration: 6.5 min (quick session)
• Focus: fillers
• Drills: 2/3 completed
• Coach: "Today you reduced fillers slightly..."
```

**Implementation:**
```python
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

class TerminalDashboard:
    def __init__(self, aggregator: DataAggregator):
        self.aggregator = aggregator
        self.console = Console()

    def render_consistency(self, days=7):
        table = Table(title="Consistency & Time")
        table.add_column("Date")
        table.add_column("Sessions")
        table.add_column("Speaking Min")

        stats = self.aggregator.get_daily_stats(days)
        for day in stats:
            table.add_row(day.date, str(day.sessions), f"{day.speaking_min:.1f}")

        self.console.print(table)

    def render_all(self):
        self.console.print(Panel("English Companion - Progress Dashboard"))
        self.render_consistency()
        self.render_grammar_fillers()
        self.render_vocabulary()
        self.render_last_session()
```

---

## 4. Data Models

### Session Summary Enhanced (ScribeSparrow extension)

```python
@dataclass
class SessionSummary:
    session_id: str
    type: str  # "quick" | "full" | "free"
    start_time: datetime
    end_time: datetime
    duration_min: float
    focus: str

    # Statistics
    total_utterances: int
    total_words: int
    drills_offered: int
    drills_completed: int
    drills_skipped: int

    # Grammar & Fillers
    grammar_signals: List[Signal]
    filler_signals: List[Signal]

    # Vocabulary
    vocab_items_seen: List[str]
    vocab_items_used: List[str]

    # Fluency
    avg_wpm: float
    median_pause_sec: float

    # Coach summary
    coach_summary: str

    # Timeline
    timeline: List[TimelineBlock]

@dataclass
class TimelineBlock:
    time_range: str  # "0-3 min"
    activity: str    # "Warm-up", "Grammar focus"
    topic: str
    drills: List[DrillRecord]
```

### Daily Statistics

```python
@dataclass
class DailyStats:
    date: str
    sessions_count: int
    session_types: Dict[str, int]  # {"quick": 1, "full": 1}
    speaking_time_min: float

    # Aggregated metrics
    total_words: int
    grammar_errors: int
    grammar_error_rate: float  # per 100 words
    filler_count: int
    filler_rate: float  # percentage

    # Vocabulary
    vocab_seen: int
    vocab_used: int

    # Fluency
    avg_wpm: float
    median_pause_sec: float
```

### Vocabulary Usage Event

```python
@dataclass
class VocabUsageEvent:
    timestamp: datetime
    session_id: str
    utterance_id: str
    notion_id: str
    word: str
    category: str
    event_type: str  # "seen" | "used_correct" | "used_incorrect"
    context: str  # User's sentence
```

---

## 5. Implementation Tasks

### Phase 1.5.1: Backend Foundation (Week 1)
- [ ] Create `src/dashboards/` structure
- [ ] Implement DataAggregator (log reading)
- [ ] Implement StatisticsCalculator (core metrics)
- [ ] Extend ScribeSparrow to generate SessionSummary with timeline
- [ ] Write unit tests for aggregation logic

### Phase 1.5.2: API Layer (Week 1-2)
- [ ] Set up FastAPI backend
- [ ] Implement `/api/consistency/*` endpoints
- [ ] Implement `/api/grammar-fillers/*` endpoints
- [ ] Implement `/api/vocabulary/*` endpoints
- [ ] Implement `/api/session/last` endpoint
- [ ] Add API documentation (OpenAPI/Swagger)

### Phase 1.5.3: Web Frontend (Week 2)
- [ ] Create HTML/CSS layout
- [ ] Implement Chart.js wrappers
- [ ] Build Dashboard 1: Consistency & Time
- [ ] Build Dashboard 2: Grammar & Fillers
- [ ] Build Dashboard 3: Vocabulary
- [ ] Build Dashboard 4: Last Session
- [ ] Responsive design (mobile-friendly)

### Phase 1.5.4: Terminal Dashboard (Week 2)
- [ ] Implement Rich-based terminal UI
- [ ] Create CLI entry point (`dashboard_cli.py`)
- [ ] Support dashboard selection (--consistency, --grammar, etc.)
- [ ] Add watch mode (auto-refresh every 30s)

### Phase 1.5.5: Integration & Deployment (Week 3)
- [ ] Create systemd service for dashboard server
- [ ] Configure auto-start on boot (after Zoo service)
- [ ] Test on Jetson (memory/performance)
- [ ] Create user documentation (DASHBOARD_GUIDE.md)
- [ ] End-to-end testing with real session data

---

## 6. Deployment

### Systemd Service

**File:** `/etc/systemd/user/companion-dashboard.service`
```ini
[Unit]
Description=English Companion Dashboard Server
After=network.target english-companion-nx.service

[Service]
Type=simple
WorkingDirectory=/home/rob/apps/english-companion-nx
ExecStart=/home/rob/apps/english-companion-nx/.venv/bin/python dashboard_server.py
Restart=on-failure
RestartSec=10
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=default.target
```

### Dashboard Server Entry Point

**File:** `dashboard_server.py`
```python
#!/usr/bin/env python3
import uvicorn
from src.dashboards.api import app
from src.core.config import Config

def main():
    config = Config()
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=config.dashboard_port,
        log_level="info"
    )

if __name__ == "__main__":
    main()
```

### Access
- **Web:** http://jetson-nx.local:8080
- **Terminal:** `./dashboard_cli.py --all`

---

## 7. Resource Allocation (Jetson Orin NX)

### Memory Budget
- **FastAPI backend:** ~100MB
- **Data aggregator cache:** ~50MB
- **Static file serving:** ~10MB
- **Total:** ~160MB (acceptable overhead)

### SSD Usage
- **Dashboard reads logs:** No writes (read-only)
- **Cache files (optional):** ~10MB, updated hourly
- **Impact:** Negligible

### Network
- **Port:** 8080 (configurable)
- **Concurrent users:** 1-2 (personal use)
- **Bandwidth:** <1MB/page load

---

## 8. Configuration (.env additions)

```bash
# Dashboard Server
DASHBOARD_ENABLED=true
DASHBOARD_PORT=8080
DASHBOARD_HOST=0.0.0.0
DASHBOARD_LOG_DIR=data/progress
DASHBOARD_CACHE_SIZE_MB=50
DASHBOARD_CACHE_TTL_SEC=3600

# Dashboard Defaults
DASHBOARD_DEFAULT_DAYS_CONSISTENCY=28
DASHBOARD_DEFAULT_DAYS_TRENDS=28
DASHBOARD_DEFAULT_DAYS_VOCAB=7
DASHBOARD_SLEEPING_VOCAB_DAYS=30
```

---

## 9. Testing Strategy

### Unit Tests
- Aggregator: Test log parsing with mock JSONL files
- Statistics: Validate metric calculations with known inputs
- API: Test endpoint responses with pytest + TestClient

### Integration Tests
- Generate synthetic session data (10 sessions)
- Query all dashboard endpoints
- Validate chart data consistency

### Performance Tests
- Load 100 sessions, measure aggregation time (<1s)
- Concurrent API requests (5 simultaneous)
- Memory leak detection (24h continuous serving)

### User Acceptance
- View dashboards after real session
- Validate trend accuracy (manual spot-check)
- Mobile responsiveness check

---

## 10. Dashboard Wireframes

### Dashboard 1: Consistency & Time
```
┌─────────────────────────────────────────────────────┐
│ 📊 Consistency & Time (Last 4 weeks)                │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Sessions Per Day                                   │
│  ┌──────────────────────────────────────┐          │
│  │ ▉▉▉ ▉▉  ▉▉▉▉ ▉▉ ▉▉▉ ... (bar chart)  │          │
│  └──────────────────────────────────────┘          │
│                                                     │
│  Speaking Time Per Day                              │
│  ┌──────────────────────────────────────┐          │
│  │  ~~/\~~/\~~~/\~~  (line chart)        │          │
│  └──────────────────────────────────────┘          │
│                                                     │
│  🔥 Streak: 5/7 days with sessions                 │
│     Solid: 5 of the last 7 days with at least one  │
│     session.                                        │
└─────────────────────────────────────────────────────┘
```

### Dashboard 2: Grammar & Fillers
```
┌─────────────────────────────────────────────────────┐
│ 📝 Grammar & Fillers Trend (Last 4 weeks)           │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Grammar Errors per 100 Words                       │
│  ┌──────────────────────────────────────┐          │
│  │  ~~\  \~~\_  (downward trend ✓)      │          │
│  │  5.2 → 4.1 → 3.8 → 3.2                │          │
│  └──────────────────────────────────────┘          │
│                                                     │
│  Error Breakdown                                    │
│  • Articles: 12    • Tense: 8                       │
│  • Prepositions: 5 • Word order: 3                  │
│                                                     │
│  Filler Rate (%)                                    │
│  ┌──────────────────────────────────────┐          │
│  │  ~~\__~\_ (improving)                 │          │
│  │  9.2% → 8.1% → 7.8%                   │          │
│  └──────────────────────────────────────┘          │
│                                                     │
│  Fluency: 110-130 WPM, median pause: 0.6s          │
└─────────────────────────────────────────────────────┘
```

### Dashboard 3: Vocabulary
```
┌─────────────────────────────────────────────────────┐
│ 📚 Vocabulary & Notion Activity (This week)         │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Active vs Passive                                  │
│  • Seen: 42  • Used: 18  (Usage: 18/42 = 43%)      │
│                                                     │
│  Top 10 "Alive" Items                               │
│  ┌───────────┬───────┬────────────┬─────────────┐  │
│  │ Expression│ Uses  │ Last Used  │ Category    │  │
│  ├───────────┼───────┼────────────┼─────────────┤  │
│  │ leverage  │ 8     │ 2024-12-15 │ Comm Verbs  │  │
│  │ facilitate│ 5     │ 2024-12-14 │ Comm Verbs  │  │
│  │ framework │ 4     │ 2024-12-15 │ Concepts    │  │
│  └───────────┴───────┴────────────┴─────────────┘  │
│                                                     │
│  Sleeping Items (30+ days dormant)                  │
│  • articulate (35 days), robust (42 days)...       │
│                                                     │
│  Review Stats                                       │
│  • Reviewed today: 5  • This week: 23               │
│  • Success: 72% easy, 28% struggled                 │
└─────────────────────────────────────────────────────┘
```

### Dashboard 4: Last Session
```
┌─────────────────────────────────────────────────────┐
│ ⏱️ Last Session Review                              │
│ Session: 2024-12-15 14:30 (Quick, 6.5 min)         │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Timeline                                           │
│  0-3 min   Warm-up (topic: e-learning)              │
│  3-6 min   Grammar focus (articles)                 │
│             ✅ Drill: Repeat corrected sentence     │
│             ⚪ Drill: Filler reduction (skipped)   │
│                                                     │
│  Focus: Fillers & article errors                    │
│  Drills: 2/3 completed                              │
│  Vocab practiced: leverage, facilitate              │
│                                                     │
│  Coach Summary                                      │
│  ┌──────────────────────────────────────┐          │
│  │ "Today you reduced fillers slightly, │          │
│  │ and you practised 2 expressions from  │          │
│  │ your Notion list. Next time, we can  │          │
│  │ build on the same topic or switch     │          │
│  │ focus to phrasal verbs."              │          │
│  └──────────────────────────────────────┘          │
└─────────────────────────────────────────────────────┘
```

---

## 11. Success Metrics

### Completion Criteria
- [ ] All 4 dashboards implemented (web + terminal)
- [ ] Dashboard server runs as systemd service
- [ ] API endpoints respond <200ms
- [ ] Dashboards load <2s on LAN
- [ ] Memory usage <200MB
- [ ] Mobile-responsive design
- [ ] User documentation complete

### Quality Metrics
- Data accuracy: 100% (no calculation errors)
- Dashboard uptime: >99% (robust error handling)
- User engagement: Used at least weekly
- Visual clarity: Charts readable on mobile

---

## 12. User Documentation

### Quick Start
```bash
# Start dashboard server
systemctl --user start companion-dashboard

# View in browser
open http://jetson-nx.local:8080

# Or terminal view
./dashboard_cli.py --all

# View specific dashboard
./dashboard_cli.py --consistency
./dashboard_cli.py --grammar
./dashboard_cli.py --vocabulary
./dashboard_cli.py --session
```

### Troubleshooting
- **Dashboard not loading:** Check service status `systemctl --user status companion-dashboard`
- **No data showing:** Ensure Zoo sessions logged to `data/progress/`
- **Slow performance:** Reduce cache TTL or clear cache

---

## 13. Future Enhancements (Post 1.5)

### Phase 1.5B (Optional)
- [ ] Export dashboard data (CSV, PDF)
- [ ] Email/notification when streaks break
- [ ] Dark mode toggle
- [ ] Customizable date ranges
- [ ] Comparison view (this week vs last week)

### Integration with Epic 2
- Prepare data models for Phase 3 advanced dashboards
- Ensure aggregator extensible for new agent signals

---

## Next Steps

1. **Review plan** - Confirm dashboard priorities
2. **Start Phase 1.5.1** - Backend foundation (DataAggregator)
3. **Build incrementally** - One dashboard at a time
4. **Test with real data** - Use Epic 1 session logs
5. **Deploy to Jetson** - systemd service setup

**Estimated completion:** 3 weeks (after Epic 1 stable)
