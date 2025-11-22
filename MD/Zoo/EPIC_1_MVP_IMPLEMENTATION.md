# Epic 1: Phase 1 MVP Implementation Plan

**Goal:** Smart but lean trainer - Core coaching functionality with grammar, fillers, vocabulary, and basic drills.

**Target:** Fully functional on Jetson Orin NX (11GB usable RAM), integrated with existing Phase 2B voice assistant.

---

## 1. Architecture Overview

### Signal Flow Architecture
```
User Speech (STT)
    ↓
[Listener Agents] → emit signals
    ↓
[OrchestratorOctopus] → collects, prioritizes, decides
    ↓
[TaskTiger] → designs drill
    ↓
[CoachCoyote] → delivers feedback (TTS)
    ↓
[Memory Agents] → update progress/vocab
```

### Integration with Phase 2B
- **Existing:** Wake word → VAD recording → Whisper → Ollama → TTS → Session management
- **New:** Insert Zoo pipeline between Whisper output and Ollama input
- **Key change:** User utterance goes through Listeners before reaching CoachCoyote/LLM

---

## 2. File Structure

```
english-companion-nx/
├── src/
│   ├── zoo/                          # NEW: Zoo agent system
│   │   ├── __init__.py
│   │   ├── signals.py               # Signal dataclasses and types
│   │   ├── orchestrator.py          # OrchestratorOctopus
│   │   │
│   │   ├── listeners/               # Passive observer agents
│   │   │   ├── __init__.py
│   │   │   ├── base.py             # BaseListener abstract class
│   │   │   ├── grammar_giraffe.py  # Grammar detection
│   │   │   ├── filler_falcon.py    # Filler tracking
│   │   │   ├── tempo_tiger.py      # WPM + pause analysis
│   │   │   └── lexi_lynx.py        # Vocabulary usage
│   │   │
│   │   ├── memory/                  # Knowledge & data agents
│   │   │   ├── __init__.py
│   │   │   ├── notion_nightingale.py   # Notion sync (read-only MVP)
│   │   │   ├── spaced_squirrel.py      # SRS scheduler
│   │   │   └── persona_panda.py        # User profile/goals
│   │   │
│   │   ├── coaching/                # Active intervention agents
│   │   │   ├── __init__.py
│   │   │   ├── coach_coyote.py     # Main conversational coach
│   │   │   ├── task_tiger.py       # Drill designer
│   │   │   ├── session_shepherd.py # Session planner
│   │   │   └── focus_falcon.py     # Focus area selector
│   │   │
│   │   └── flow/                    # State & session management
│   │       ├── __init__.py
│   │       ├── day_dolphin.py      # Day state machine
│   │       ├── scribe_sparrow.py   # Session logger
│   │       └── boundary_bison.py   # Mode/intensity manager
│   │
│   ├── core/
│   │   └── zoo_config.py           # Zoo-specific configuration
│   │
│   └── data/                        # NEW: Local data stores
│       ├── vocab/                   # Notion cache + usage logs
│       ├── progress/                # SRS schedules, session logs
│       └── profile/                 # User goals, preferences
│
├── voice_assistant_zoo.py          # NEW: Zoo-enabled main entry
├── test_zoo_*.py                   # Zoo component tests
└── .env                            # Add Zoo config vars
```

---

## 3. Core Components

### 3.1 Signal System (`src/zoo/signals.py`)

**Signal Dataclass:**
```python
@dataclass
class Signal:
    source: str              # Agent name (e.g., "GrammarGiraffe")
    type: str                # Signal category (e.g., "grammar_error", "filler")
    severity: float          # 0.0-1.0 (1.0 = critical)
    scope: str               # "utterance" | "session" | "trend"
    realtime_desirable: bool # Should act on now vs buffer?
    data: dict               # Payload (error details, filler count, etc.)
    timestamp: float         # Unix timestamp
    utterance_id: str        # Link to specific utterance
```

**Signal Types:**
- `grammar_error` - Specific mistake (articles, tense, word order)
- `filler_detected` - Filler word usage
- `vocab_opportunity` - Could use Notion vocab here
- `vocab_used` - Target vocab used correctly/incorrectly
- `tempo_issue` - Too fast/slow, long pauses

### 3.2 OrchestratorOctopus (`src/zoo/orchestrator.py`)

**Responsibilities:**
- Collect signals from all listeners for each utterance
- Score/prioritize signals based on:
  - Session focus (from FocusFalcon)
  - Coach mode intensity (from BoundaryBison)
  - Recent drill frequency (don't overwhelm)
  - Signal severity
- Decide action:
  - **Real-time queue:** Max 1 drill per utterance
  - **Session buffer:** Store for end-of-session summary
  - **Trend store:** Aggregate for long-term tracking
- Send drill requests to TaskTiger

**Key Methods:**
```python
class OrchestratorOctopus:
    def process_utterance(utterance, signals: List[Signal]) -> Action
    def should_drill_now(signal, context) -> bool
    def buffer_for_later(signal)
    def update_trends(signal)
```

**Action Types:**
- `DRILL_NOW` - Immediate intervention
- `BUFFER` - Save for session end
- `IGNORE` - Low priority, log only
- `PASS_THROUGH` - Normal conversation continues

### 3.3 Listener Agents

#### GrammarGiraffe (`src/zoo/listeners/grammar_giraffe.py`)
**Detection Strategy (MVP):**
- Use LLM (llama3.2:3b) with grammar-focused prompt
- Parse response for error categories:
  - Articles (a/an/the)
  - Tense errors
  - Word order
  - Subject-verb agreement
  - Prepositions
- Emit signal per error found

**Resource:** ~500ms LLM call per utterance (acceptable)

#### FillerFalcon (`src/zoo/listeners/filler_falcon.py`)
**Detection Strategy:**
- Simple regex/token matching: `uhm, uh, um, like, you know, basically, actually`
- Count per utterance, calculate rate (fillers/minute)
- Emit signal if rate exceeds threshold (e.g., >3/min)

**Resource:** <10ms, negligible

#### TempoTiger (`src/zoo/listeners/tempo_tiger.py`)
**Detection Strategy (MVP - Basic):**
- Use Whisper timestamps (word-level if available)
- Calculate WPM (words per minute)
- Detect pauses >1.5s between words
- Emit signals for:
  - Too slow (<100 WPM)
  - Too fast (>180 WPM)
  - Long pauses (>2s)

**Resource:** ~50ms timestamp processing

#### LexiLynx (`src/zoo/listeners/lexi_lynx.py`)
**Detection Strategy:**
- Load Notion vocab cache (NotionNightingale provides)
- Match user utterance against target words/collocations
- Emit signals:
  - `vocab_used` - Target word used correctly
  - `vocab_missed` - Could have used target vocab (context match)
  - `vocab_error` - Target word used incorrectly

**Resource:** ~100ms fuzzy matching against vocab DB

---

### 3.4 Memory Agents

#### NotionNightingale (`src/zoo/memory/notion_nightingale.py`)
**MVP Scope: Read-Only**
- Sync Notion vocab database → local JSON cache
- Refresh: Daily at DAY_BOOT (or manual trigger)
- Cache structure:
```json
{
  "words": [
    {
      "id": "notion_page_id",
      "word": "leverage",
      "type": "verb",
      "definition": "use strategically",
      "example": "We can leverage our expertise",
      "status": "learning",
      "added_date": "2024-12-01",
      "notion_url": "https://..."
    }
  ],
  "collocations": [...]
}
```

**Resource:** Notion API call at boot (~2-3s), cached to SSD (~1MB)

#### SpacedSquirrel (`src/zoo/memory/spaced_squirrel.py`)
**MVP: Simple Date-Based SRS**
- Algorithm: SM-2 simplified
  - Items: vocabulary, grammar patterns, drill types
  - Review intervals: 1d, 3d, 7d, 14d, 30d
  - Success → next interval; Failure → restart
- Store in JSON: `data/progress/srs_schedule.json`
- Methods:
  - `get_due_today() -> List[Item]`
  - `mark_reviewed(item, success: bool)`
  - `add_item(item, initial_interval=1d)`

**Resource:** <50ms, SSD write buffered (5-min intervals)

#### PersonaPanda (`src/zoo/memory/persona_panda.py`)
**MVP: Static Profile**
- Load from `data/profile/user_profile.json`:
```json
{
  "cefr_target": "C1",
  "native_language": "German",
  "accent_preference": "American",
  "coach_intensity": "normal",
  "weekly_focus": "business_communication",
  "topics": ["e-learning", "3D", "leadership"],
  "availability": {"start": "09:00", "end": "17:00"}
}
```
- Methods:
  - `get_profile() -> Profile`
  - `update_intensity(mode: str)`

**Resource:** <10ms, static file

---

### 3.5 Coaching Agents

#### CoachCoyote (`src/zoo/coaching/coach_coyote.py`)
**Role: Single LLM Voice**
- Replaces direct Ollama call in Phase 2B
- Receives:
  - User utterance
  - Conversation context (last 20 exchanges)
  - Current drill (if any) from TaskTiger
  - Session focus from FocusFalcon
  - User profile from PersonaPanda
- Generates response with:
  - Natural conversation flow
  - Drill delivery (if applicable)
  - Tone adapted to coach_intensity

**Prompt Template:**
```
You are Rob's English conversation coach.

Current focus: {focus}
Coach mode: {intensity}
Profile: {cefr_target}, prefers {accent_preference}

{drill_instruction_if_any}

Conversation history:
{context}

User: {utterance}

Respond naturally. {drill_delivery_guidance}
```

**Resource:** ~6-8s LLM call (same as Phase 2B)

#### TaskTiger (`src/zoo/coaching/task_tiger.py`)
**MVP: 3 Basic Drill Types**

1. **Filler Drill:**
   - "Say that again without 'um' or 'like'"
   - Expects: User re-attempts sentence

2. **Grammar Drill:**
   - "Try this instead: [corrected sentence]. Repeat it."
   - Expects: User repeats

3. **Vocab Drill:**
   - "Can you use '{notion_word}' in a new sentence?"
   - Expects: User creates example

**Methods:**
```python
class TaskTiger:
    def design_drill(signal: Signal, context) -> Drill
    def validate_attempt(drill: Drill, response: str) -> bool
```

**Resource:** <100ms drill generation

#### SessionShepherd (`src/zoo/coaching/session_shepherd.py`)
**MVP: Simple Session Planning**
- At DAY_BOOT, creates `today_plan`:
  - Review items from SpacedSquirrel
  - 1 focus area from FocusFalcon
- Session types:
  - **Quick (5-7 min):** 2-3 review items + focused drills
  - **Full (15-20 min):** 5-7 review items + broader practice
  - **Free:** No structured plan, but signals still active

**Methods:**
```python
class SessionShepherd:
    def build_daily_plan() -> DailyPlan
    def select_session_subset(type: str) -> SessionPlan
    def mark_completed(item)
```

#### FocusFalcon (`src/zoo/coaching/focus_falcon.py`)
**MVP: Single Focus Per Session**
- Choose 1 focus from:
  - `fillers` - Reduce filler usage
  - `grammar` - Grammar accuracy
  - `vocab` - Use Notion vocabulary
- Selection logic:
  - Check ScribeSparrow's recent stats
  - Rotate focus areas (avoid repetition)
  - Respect PersonaPanda's weekly_focus if set

**Methods:**
```python
class FocusFalcon:
    def select_focus(recent_stats) -> str
    def should_rotate() -> bool
```

---

### 3.6 Flow Control Agents

#### DayDolphin (`src/zoo/flow/day_dolphin.py`)
**State Machine:**
```
DAY_BOOT → WAITING_FOR_USER → IN_SESSION → FREE_CONVERSATION → DAY_OVER
                                    ↓              ↑
                                    └──────────────┘
                                  (can toggle back)
```

**Triggers:**
- `DAY_BOOT`: Service starts in 9-5 window
- `WAITING_FOR_USER`: Plan ready, waiting for first utterance
- `IN_SESSION`: Structured session active (quick/full)
- `FREE_CONVERSATION`: Casual chat, signals passive
- `DAY_OVER`: After 5pm or shutdown

**Methods:**
```python
class DayDolphin:
    def boot()
    def start_session(type: str)
    def end_session()
    def transition_to(state: str)
    def get_state() -> str
```

#### ScribeSparrow (`src/zoo/flow/scribe_sparrow.py`)
**Logging Strategy:**
- **Per utterance:** JSONL append (buffered, 5-min flush)
  ```json
  {
    "timestamp": "2024-12-15T10:23:45",
    "utterance": "I think we should um leverage this",
    "signals": [{"source": "FillerFalcon", "type": "filler_detected", ...}],
    "drill_offered": {"type": "filler", "completed": true},
    "duration_ms": 3200
  }
  ```
- **Session summary:** JSON file per session
  ```json
  {
    "session_id": "2024-12-15_1023",
    "type": "quick",
    "duration_min": 6.5,
    "focus": "fillers",
    "drills_offered": 3,
    "drills_completed": 2,
    "vocab_used": ["leverage", "facilitate"],
    "stats": {"filler_rate": 2.1, "wpm": 145}
  }
  ```

**Resource:** Buffered writes, ~100KB/day

#### BoundaryBison (`src/zoo/flow/boundary_bison.py`)
**MVP: Simple Mode Control**
- Coach modes:
  - `off` - No drills, pure conversation
  - `soft` - Max 1 drill per 5 minutes
  - `normal` - Max 1 drill per utterance

**Methods:**
```python
class BoundaryBison:
    def get_mode() -> str
    def set_mode(mode: str)
    def can_drill_now(last_drill_time) -> bool
```

---

## 4. Implementation Tasks

### Phase 1.1: Foundation (Week 1) ✅ COMPLETE
- [x] Create `src/zoo/` directory structure
- [x] Implement `signals.py` (Signal dataclass, types)
- [x] Implement `BaseListener` abstract class
- [x] Implement DayDolphin state machine
- [x] Implement PersonaPanda (static profile loader)
- [x] Write unit tests for Signal and DayDolphin

### Phase 1.2: Listeners (Week 2) ✅ COMPLETE
- [x] Implement FillerFalcon (regex-based)
- [x] Implement GrammarGiraffe (LLM-based)
- [x] Implement TempoTiger (basic WPM + pauses)
- [x] Implement LexiLynx (vocab matching)
- [x] Write listener integration tests

### Phase 1.3: Memory & Planning (Week 2-3) ✅ COMPLETE
- [x] Implement NotionNightingale (read-only sync) ✅ COMPLETE
- [x] Implement SpacedSquirrel (simple SRS) ✅ COMPLETE
- [x] Implement SessionShepherd (daily planner) - Implementation done, tests successful ✅ COMPLETE
- [x] Implement FocusFalcon (focus selector) - Implementation done, tests successful ✅ COMPLETE
- [x] Test Notion integration end-to-end ✅ COMPLETE

### Phase 1.4: Orchestration (Week 3)
- [x] Implement OrchestratorOctopus (signal processing)
- [x] Implement signal scoring/prioritization logic
- [x] Implement drill-now vs buffer decision logic
- [x] Test orchestration with mock signals

### Phase 1.5: Coaching (Week 4)
- [ ] Implement TaskTiger (3 drill types)
- [ ] Implement CoachCoyote (LLM prompt integration)
- [ ] Implement drill validation logic
- [ ] Test drill delivery end-to-end

### Phase 1.6: Logging & Flow (Week 4-5)
- [ ] Implement ScribeSparrow (utterance + session logging)
- [ ] Implement BoundaryBison (mode control)
- [ ] Create session summary generation
- [ ] Test full session flow (boot → session → end)

### Phase 1.7: Integration with Phase 2B (Week 5)
- [ ] Create `voice_assistant_zoo.py` (modified main entry)
- [ ] Integrate Zoo pipeline between Whisper → Ollama
- [ ] Test wake word → recording → Zoo → TTS flow
- [ ] Memory usage profiling (must fit in 11GB)

### Phase 1.8: Testing & Refinement (Week 6)
- [ ] End-to-end system tests (full conversations)
- [ ] Performance tuning (latency < 10s total)
- [ ] SSD write monitoring (< 200MB/day)
- [ ] User acceptance testing (real sessions)

---

## 5. Data Models

### Session Log Entry (JSONL)
```json
{
  "timestamp": "2024-12-15T10:23:45.123Z",
  "session_id": "2024-12-15_1023",
  "utterance_id": "uuid-1234",
  "text": "I think we should um leverage this opportunity",
  "duration_ms": 3200,
  "signals": [
    {
      "source": "FillerFalcon",
      "type": "filler_detected",
      "severity": 0.6,
      "data": {"filler": "um", "position": 4}
    },
    {
      "source": "LexiLynx",
      "type": "vocab_used",
      "severity": 0.0,
      "data": {"word": "leverage", "correct": true}
    }
  ],
  "action": {
    "type": "drill",
    "drill_type": "filler",
    "completed": true,
    "attempt": "I think we should leverage this opportunity"
  }
}
```

### SRS Schedule (JSON)
```json
{
  "items": [
    {
      "id": "vocab_leverage",
      "type": "vocabulary",
      "content": "leverage (verb)",
      "interval_days": 7,
      "next_review": "2024-12-22",
      "ease_factor": 2.5,
      "repetitions": 3
    },
    {
      "id": "grammar_articles_a_an",
      "type": "grammar",
      "content": "a vs an usage",
      "interval_days": 3,
      "next_review": "2024-12-18",
      "ease_factor": 2.0,
      "repetitions": 1
    }
  ]
}
```

### Daily Plan (JSON)
```json
{
  "date": "2024-12-15",
  "focus": "fillers",
  "review_due": ["vocab_leverage", "grammar_articles_a_an"],
  "session_plans": {
    "quick": {
      "duration_target_min": 7,
      "review_items": 2,
      "drill_budget": 3
    },
    "full": {
      "duration_target_min": 20,
      "review_items": 5,
      "drill_budget": 7
    }
  }
}
```

---

## 6. Configuration (.env additions)

```bash
# Zoo System
ZOO_ENABLED=true
ZOO_COACH_MODE=normal  # off | soft | normal
ZOO_DAILY_START=09:00
ZOO_DAILY_END=17:00

# Notion Integration
NOTION_API_KEY=secret_xxx
NOTION_VOCAB_DB_ID=abc123
NOTION_SYNC_INTERVAL_HOURS=24

# Agent Tuning
ORCHESTRATOR_MAX_DRILLS_PER_MIN=1
FILLER_THRESHOLD_PER_MIN=3
TEMPO_MIN_WPM=100
TEMPO_MAX_WPM=180
GRAMMAR_SEVERITY_THRESHOLD=0.5

# Memory Constraints
ZOO_MAX_CONTEXT_EXCHANGES=20
ZOO_LOG_FLUSH_INTERVAL_SEC=300
ZOO_SESSION_BUFFER_SIZE=100
```

---

## 7. Resource Allocation (Jetson Orin NX)

### Memory Budget (11GB total usable)
- **Phase 2B base:** ~8GB (Whisper, Ollama, TTS, wake word)
- **Zoo overhead:**
  - Listeners: ~200MB (GrammarGiraffe LLM calls reuse Ollama)
  - Memory agents: ~100MB (vocab cache, SRS data)
  - Orchestrator: ~50MB (signal buffers)
  - Logging: ~50MB (JSONL buffers)
- **Total estimated:** ~8.4GB (leaves 2.6GB headroom)

### SSD Write Budget (200MB/day target)
- **Utterance logs:** ~50KB/day (5-min buffered flush)
- **Session summaries:** ~10KB/day
- **SRS updates:** ~5KB/day
- **Notion cache:** ~1MB/day (daily sync)
- **Total estimated:** ~1.1MB/day (well under limit)

### Latency Budget (per utterance)
- STT (Whisper): ~1.5s
- Listeners (parallel): ~0.5s (GrammarGiraffe slowest)
- Orchestrator: ~0.1s
- TaskTiger: ~0.1s
- CoachCoyote (LLM): ~6s
- TTS: ~2.5s
- **Total:** ~10.7s (acceptable)

---

## 8. Testing Strategy

### Unit Tests
- All agents have standalone tests
- Mock signal generation
- Mock LLM responses (for GrammarGiraffe, CoachCoyote)

### Integration Tests
- Listener → Orchestrator → TaskTiger flow
- SessionShepherd → FocusFalcon → CoachCoyote planning
- NotionNightingale → LexiLynx vocab matching

### System Tests
- Full conversation sessions (scripted)
- Memory leak detection (24h continuous run)
- SSD write monitoring
- Latency profiling

### User Acceptance
- Real 15-min conversation sessions
- Feedback on drill quality/timing
- Focus area effectiveness

---

## 9. Migration from Phase 2B

### Changes to `voice_assistant.py`
```python
# OLD: Direct Ollama call
response = llm_client.generate(user_text, context)

# NEW: Zoo pipeline
signals = zoo.process_utterance(user_text)
action = orchestrator.decide(signals)
if action.type == "drill":
    response = coach_coyote.deliver_drill(action.drill, context)
else:
    response = coach_coyote.converse(user_text, context)
```

### Backward Compatibility
- Keep `conversation_prototype.py` as non-Zoo fallback
- Zoo can be disabled via `ZOO_ENABLED=false`
- Gradual rollout: Test listeners first before full orchestration

---

## 10. Success Metrics

### MVP Completion Criteria
- [ ] All 15 agents implemented and tested
- [ ] Full session flow works end-to-end
- [ ] Memory usage < 9GB during sessions
- [ ] SSD writes < 50MB/day
- [ ] Average response latency < 12s
- [ ] User can complete 15-min session without crashes
- [ ] Notion vocab integration working (read-only)
- [ ] Session logs generated correctly

### Quality Metrics
- Grammar detection accuracy > 80%
- Filler detection accuracy > 95%
- Vocab matching precision > 90%
- Drill completion rate > 60%
- User satisfaction rating > 4/5

---

## 11. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| GrammarGiraffe too slow (LLM) | High latency | Use smaller LLM, cache common errors |
| Memory overflow | System crash | Aggressive context pruning, monitoring |
| SSD wear from logging | Hardware failure | Buffered writes, tmpfs for temp data |
| Notion API rate limits | Sync failure | Daily sync only, local cache fallback |
| Too many drills annoy user | Poor UX | BoundaryBison strict throttling |
| LexiLynx false positives | Bad vocab drills | Fuzzy matching threshold tuning |

---

## Next Steps

1. **Review this plan** - Confirm architecture and scope
2. **Set up project structure** - Create directories and base classes
3. **Start with Phase 1.1** - Foundation (DayDolphin, Signals, PersonaPanda)
4. **Incremental testing** - Test each agent independently before integration
5. **Weekly progress reviews** - Adjust timeline as needed

**Estimated completion:** 6 weeks (assuming 10-15 hours/week)
