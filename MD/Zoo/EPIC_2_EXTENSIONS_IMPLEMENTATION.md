# Epic 2: Phase 2 Extensions Implementation Plan

**Goal:** Full-blown excellent coach - Add depth with actors, listening comprehension, pronunciation, motivation tracking, learning strategies, and richer context awareness.

**Prerequisites:** Epic 1 (MVP) fully operational and stable on Jetson Orin NX.

---

## 1. Architecture Additions

### Extended Signal Flow
```
User Speech (STT)
    ↓
[Phase 1 Listeners] + [Phase 2 Listeners] → more diverse signals
    ↓
[OrchestratorOctopus] → richer prioritization with affective state
    ↓
[Extended TaskTiger] → 8+ drill types (pronunciation, listening, shadowing)
    ↓
[CoachCoyote] → context-aware delivery with actor clips
    ↓
[Extended Memory] → topic history, actor phrases, learning strategies
```

### New Capabilities
- **Actor-based learning:** Shadowing exercises with real clips
- **Listening comprehension:** Gist questions, dictation, comprehension checks
- **Pronunciation coaching:** Stress/intonation feedback
- **Affective monitoring:** Detect frustration, adjust intensity
- **Learning strategies:** Explicit metacognitive coaching
- **Topic continuity:** Remember past themes for relevant practice

---

## 2. File Structure Additions

```
english-companion-nx/
├── src/
│   ├── zoo/
│   │   ├── listeners/
│   │   │   ├── echo_eagle.py            # NEW: Overuse detection
│   │   │   ├── pattern_panther.py       # NEW: Recurring structures
│   │   │   ├── pronunciation_penguin.py # NEW: Pronunciation/stress
│   │   │   └── empathy_elephant.py      # NEW: Affective state
│   │   │
│   │   ├── memory/
│   │   │   ├── script_spider.py         # NEW: Actor clip store
│   │   │   ├── story_stork.py           # NEW: Topic history
│   │   │   └── crawler_crab.py          # NEW: Web content fetcher
│   │   │
│   │   ├── coaching/
│   │   │   ├── actor_albatross.py       # NEW: Shadowing coach
│   │   │   ├── comprehension_cougar.py  # NEW: Listening exercises
│   │   │   └── strategy_swan.py         # NEW: Metacognitive coaching
│   │   │
│   │   └── orchestrator.py              # EXTENDED: Affective awareness
│   │
│   ├── media/                           # NEW: Audio/video clips
│   │   ├── actors/                      # Actor clips (MP3/WAV)
│   │   │   ├── denzel_washington/
│   │   │   ├── morgan_freeman/
│   │   │   └── ...
│   │   └── temp/                        # Temporary clip processing
│   │
│   └── data/
│       ├── actors/                      # Actor metadata + transcripts
│       ├── topics/                      # Topic history + mined content
│       └── strategies/                  # Learning strategy library
│
├── tools/                               # NEW: Utilities
│   ├── actor_clip_importer.py          # Import/process actor clips
│   ├── web_content_scraper.py          # CrawlerCrab automation
│   └── pronunciation_analyzer.py       # Offline pronunciation analysis
│
└── test_zoo_phase2_*.py                # Phase 2 tests
```

---

## 3. New Listener Agents

### 3.1 EchoEagle (`src/zoo/listeners/echo_eagle.py`)

**Purpose:** Detect overused words/phrases that make speech vague or repetitive.

**Target Patterns:**
- Vague intensifiers: *very, really, quite, pretty, so*
- Discourse markers: *actually, basically, honestly, literally, obviously*
- Hedges: *kind of, sort of, I think, maybe, probably*
- Transition overuse: *and then, and so, and like*
- Personal patterns: Track user-specific repetitions (e.g., "in this case" 5x in session)

**Detection Strategy:**
- Token frequency analysis per session
- Compare against baseline frequency norms
- Track user-specific overuse patterns (PersonaPanda history)
- Emit signal when usage exceeds 2x normal frequency

**Signal Example:**
```python
Signal(
    source="EchoEagle",
    type="overuse_detected",
    severity=0.5,
    scope="session",
    realtime_desirable=False,  # Better as session summary
    data={
        "phrase": "actually",
        "count": 7,
        "expected_max": 3,
        "suggestions": ["in fact", "as it happens", "to be precise"]
    }
)
```

**Resource:** ~100ms per utterance (token frequency)

---

### 3.2 PatternPanther (`src/zoo/listeners/pattern_panther.py`)

**Purpose:** Identify recurring sentence structures and German→English transfer patterns.

**Pattern Categories:**
1. **Sentence structure:**
   - Overuse of "I think that..." starters
   - Simple SVO repetition (lacks variety)
   - Rare use of inversion/fronting

2. **Transfer errors (German):**
   - False cognates: *become* (bekommen) instead of *get*
   - Word order: *"I have yesterday spoken"* (German perfect tense order)
   - Article misuse: *"In the office"* when *"At the office"* is standard

3. **Register inconsistency:**
   - Mixing formal/informal (e.g., "gonna" + "nevertheless")

**Detection Strategy:**
- Parse sentence structures (dependency parsing via spaCy)
- Track structure frequency distribution
- Maintain German→English error pattern database
- Emit signal when same structure used 3+ times in session

**Signal Example:**
```python
Signal(
    source="PatternPanther",
    type="pattern_recurring",
    severity=0.4,
    scope="session",
    realtime_desirable=False,
    data={
        "pattern": "I think + [clause]",
        "count": 5,
        "alternatives": ["In my view", "It seems to me", "I'd argue that"],
        "transfer_type": None
    }
)
```

**Resource:** ~300ms (spaCy parsing, requires CPU model load ~100MB)

---

### 3.3 PronunciationPenguin (`src/zoo/listeners/pronunciation_penguin.py`)

**Purpose:** Detect pronunciation errors, word stress issues, and prosody problems.

**Detection Strategy:**
- **Phonetic analysis:** Compare Whisper confidence scores (low confidence = likely mispronunciation)
- **Misheard words:** Track words consistently misrecognized by STT
- **Stress patterns:** Use forced alignment (Montreal Forced Aligner or similar)
- **Common German accent issues:**
  - /w/ vs /v/ confusion (*wine* → *vine*)
  - /θ/ (th) → /s/ or /t/ (*think* → *sink* or *tink*)
  - Final devoicing (*bad* → *bat*)

**MVP Approach (Phase 2A):**
- Start simple: Track Whisper low-confidence words
- Build pronunciation error database from misrecognitions
- Defer forced alignment to Phase 2B (too resource-heavy for MVP)

**Signal Example:**
```python
Signal(
    source="PronunciationPenguin",
    type="pronunciation_issue",
    severity=0.6,
    scope="utterance",
    realtime_desirable=True,  # Can drill immediately
    data={
        "word": "weather",
        "misheard_as": "wetter",
        "confidence": 0.45,
        "phoneme_issue": "/w/ vs /v/",
        "drill_suggestion": "minimal_pair"  # weather/wetter, wine/vine
    }
)
```

**Resource:** ~200ms (Whisper confidence parsing), forced alignment adds ~1s if enabled

---

### 3.4 EmpathyElephant (`src/zoo/listeners/empathy_elephant.py`)

**Purpose:** Monitor affective state and motivation to adjust coaching intensity.

**Indicators:**
1. **Drill engagement:**
   - Skipped drills (user ignores TaskTiger requests)
   - Very short responses (<5 words) after drill
   - Repeated "I don't know" / "skip this"

2. **Self-critical language:**
   - "I can't do this"
   - "This is too hard"
   - "I always mess this up"

3. **Energy markers:**
   - Response latency (long pauses before answering)
   - Utterance length trend (declining over session)
   - Vocal energy (future: prosody analysis)

**Detection Strategy:**
- Pattern matching for self-critical phrases
- Track drill skip rate (>50% = frustration signal)
- Monitor utterance length variance (sharp drop = fatigue)

**Signal Example:**
```python
Signal(
    source="EmpathyElephant",
    type="low_motivation",
    severity=0.7,
    scope="session",
    realtime_desirable=True,  # Adjust intensity NOW
    data={
        "indicators": ["drill_skip_rate_high", "self_critical_language"],
        "drill_skips": 4,
        "total_drills": 6,
        "self_critical_count": 2,
        "recommendation": "reduce_intensity"  # → BoundaryBison
    }
)
```

**Action:** OrchestratorOctopus → BoundaryBison → temporarily switch to `soft` mode

**Resource:** ~50ms (pattern matching)

---

## 4. New Memory Agents

### 4.1 ScriptSpider (`src/zoo/memory/script_spider.py`)

**Purpose:** Store and index actor clips, transcripts, and mined expressions.

**Data Model:**
```json
{
  "clips": [
    {
      "id": "denzel_equalizer_cafe",
      "actor": "Denzel Washington",
      "source": "The Equalizer (2014)",
      "file_path": "media/actors/denzel_washington/equalizer_cafe.mp3",
      "duration_sec": 12.5,
      "transcript": "Sometimes you gotta do what you gotta do, even if it's not by the book.",
      "phrases": [
        {
          "text": "gotta do what you gotta do",
          "type": "idiom",
          "meaning": "necessity justifies actions"
        },
        {
          "text": "not by the book",
          "type": "idiom",
          "meaning": "unconventional, breaking rules"
        }
      ],
      "tags": ["leadership", "decision-making", "pragmatism"],
      "difficulty": "B2",
      "accent": "American"
    }
  ]
}
```

**Methods:**
```python
class ScriptSpider:
    def index_clip(clip_path, actor, source) -> Clip
    def search_by_tags(tags: List[str]) -> List[Clip]
    def search_by_phrase(phrase: str) -> List[Clip]
    def get_random_clip(difficulty: str, accent: str) -> Clip
    def mine_expressions(transcript: str) -> List[Expression]
```

**Resource:** ~50MB index, ~1GB actor clips (SSD storage acceptable)

---

### 4.2 StoryStork (`src/zoo/memory/story_stork.py`)

**Purpose:** Remember past conversation topics and themes for continuity.

**Data Model:**
```json
{
  "topics": [
    {
      "date": "2024-12-10",
      "session_id": "2024-12-10_1430",
      "main_topics": ["e-learning", "course design", "engagement"],
      "keywords": ["LMS", "microlearning", "gamification", "learner motivation"],
      "context": "Discussed challenges in enterprise e-learning platforms"
    }
  ],
  "themes": {
    "e-learning": {
      "frequency": 15,
      "last_discussed": "2024-12-15",
      "sub_topics": ["course design", "engagement", "assessment"],
      "vocab_used": ["learner-centric", "scaffolding", "formative assessment"]
    }
  }
}
```

**Methods:**
```python
class StoryStork:
    def log_topic(session_id, topics, keywords)
    def get_recent_themes(days=7) -> List[Theme]
    def suggest_related_topics(current_topic) -> List[str]
    def get_vocab_for_theme(theme) -> List[str]
```

**Use Case:** CoachCoyote references past topics: *"Last week we talked about learner engagement. How did that meeting go?"*

**Resource:** ~10MB topic history (JSONL)

---

### 4.3 CrawlerCrab (`src/zoo/memory/crawler_crab.py`)

**Purpose:** Fetch web/social content for real-world material (articles, videos, quotes).

**Sources:**
- YouTube clips (actor interviews, TED talks)
- News articles (business, tech, leadership)
- LinkedIn posts (professional communication examples)
- Reddit threads (informal discourse)

**Workflow:**
1. User provides URL or topic keyword
2. CrawlerCrab fetches content
3. Extracts text, audio (yt-dlp), or key quotes
4. Hands to ScriptSpider (if actor-related) or StoryStork (if topic content)

**Methods:**
```python
class CrawlerCrab:
    def fetch_youtube(url) -> VideoContent
    def fetch_article(url) -> ArticleContent
    def search_content(query, source_type) -> List[Content]
```

**Resource:** Network I/O, ~100MB temp storage for downloads

---

## 5. New Coaching Agents

### 5.1 ActorAlbatross (`src/zoo/coaching/actor_albatross.py`)

**Purpose:** Run shadowing exercises with actor clips and mine reusable phrases.

**Drill Types:**
1. **Shadow & Repeat:**
   - Play clip → User repeats (with or without text)
   - Compare timing/prosody

2. **Phrase Extraction:**
   - *"Listen to how Denzel says 'gotta do what you gotta do'. Now use it in your own sentence."*

3. **Accent Mirroring:**
   - Focus on specific phonemes/stress patterns from clip

**Methods:**
```python
class ActorAlbatross:
    def select_clip(user_level, focus_area, actor_pref) -> Clip
    def run_shadowing_drill(clip: Clip) -> Drill
    def extract_target_phrase(clip: Clip) -> str
    def compare_prosody(clip_audio, user_audio) -> Score  # Future: DTW alignment
```

**Integration:**
- ScriptSpider provides clips
- TaskTiger delegates shadowing drills to ActorAlbatross
- CoachCoyote delivers: *"Let's practice with this clip from The Equalizer..."*

**Resource:** ~500ms clip playback + TTS delivery

---

### 5.2 ComprehensionCougar (`src/zoo/coaching/comprehension_cougar.py`)

**Purpose:** Run listening comprehension exercises (gist, detail, dictation).

**Drill Types:**
1. **Gist Questions:**
   - Play clip → *"What was the main point?"*
   - User answers → LLM evaluates

2. **Detail Questions:**
   - *"What did he say about X?"*
   - Requires specific information recall

3. **Keyword Dictation:**
   - *"Listen again. What word did he use instead of 'problem'?"*
   - User transcribes specific word

4. **Shadowing Comprehension:**
   - Shadow clip → Then answer question (dual task)

**Methods:**
```python
class ComprehensionCougar:
    def generate_gist_question(clip: Clip) -> str
    def generate_detail_questions(clip: Clip, n=3) -> List[str]
    def evaluate_answer(question, user_answer, transcript) -> bool
```

**Integration:**
- Uses ScriptSpider clips
- Can also use StoryStork topics (e.g., play podcast segment on e-learning)

**Resource:** ~5s LLM evaluation per answer

---

### 5.3 StrategySwan (`src/zoo/coaching/strategy_swan.py`)

**Purpose:** Teach explicit learning strategies (metacognitive coaching).

**Strategy Types:**
1. **Paraphrasing:**
   - *"Instead of saying it the same way, try explaining it differently."*

2. **Chunking:**
   - *"Break this sentence into smaller parts if it's too complex."*

3. **Self-correction:**
   - *"Did you notice the grammar issue? Try fixing it yourself first."*

4. **Shadowing technique:**
   - *"Focus on mimicking the rhythm, not just the words."*

5. **Vocabulary anchoring:**
   - *"Create a mental image for 'leverage' - maybe a lever lifting something heavy."*

**Delivery:**
- Short "strategy moments" mid-session (30-60 seconds)
- OrchestratorOctopus triggers when user struggles repeatedly with same issue
- PersonaPanda tracks which strategies user has learned

**Methods:**
```python
class StrategySwan:
    def suggest_strategy(struggle_type) -> Strategy
    def deliver_strategy_moment(strategy: Strategy, context) -> str
    def has_learned(strategy_id) -> bool
```

**Resource:** <100ms (strategy lookup)

---

## 6. Extended Agent Capabilities

### 6.1 TaskTiger Extensions

**New Drill Types (Total: 8+):**

4. **Pronunciation Drill:**
   - Minimal pairs: *"Say both: weather / wetter"*
   - Stress practice: *"Say 'REcord' (noun) vs 're-CORD' (verb)"*

5. **Shadowing Drill:**
   - Delegated to ActorAlbatross

6. **Listening Comprehension Drill:**
   - Delegated to ComprehensionCougar

7. **Paraphrase Drill:**
   - *"Say the same thing another way."*
   - StrategySwan validates alternative phrasing

8. **Register Shift Drill:**
   - *"Make this more formal/informal."*
   - E.g., *"I gotta go"* → *"I must leave now"*

---

### 6.2 OrchestratorOctopus Extensions

**New Prioritization Factors:**
- **Affective state:** If EmpathyElephant signals low motivation, reduce drill intensity
- **Topic continuity:** Prefer drills related to StoryStork's recent themes
- **Strategy fit:** Align drills with StrategySwan's active learning goals

**Enhanced Decision Logic:**
```python
def decide_action(signals, context):
    # Check affective state first
    if any(s.source == "EmpathyElephant" and s.severity > 0.6 for s in signals):
        BoundaryBison.reduce_intensity()
        return Action(type="BUFFER_ALL")  # Skip drills, just converse

    # Prioritize pronunciation if recurring issue
    pronunciation_signals = [s for s in signals if s.source == "PronunciationPenguin"]
    if len(pronunciation_signals) >= 3:  # 3+ pronunciation issues
        return Action(type="DRILL_NOW", drill_type="pronunciation")

    # Continue with Phase 1 logic...
```

---

### 6.3 FocusFalcon Extensions

**Weekly Themes:**
- Not just session-level focus, but week-long themes:
  - **Week 1:** Filler reduction
  - **Week 2:** Advanced adjectives (replacing "very good", "very bad")
  - **Week 3:** Phrasal verbs
  - **Week 4:** Register switching (formal/informal)

**Integration with PersonaPanda:**
- User can set explicit weekly focus
- FocusFalcon auto-suggests next theme based on ScribeSparrow stats

---

### 6.4 BoundaryBison Extensions

**Weekly Check-ins:**
- Every Monday: *"What's your focus this week? Any big meetings coming up?"*
- Adjust intensity based on user's schedule:
  - Big presentation Friday → increase intensity Mon-Wed
  - Light week → more experimental/creative drills

**Dynamic Intensity:**
- EmpathyElephant signals → temporary `soft` mode
- High drill completion rate → offer `intense` mode

---

## 7. Implementation Tasks

### Phase 2.1: Advanced Listeners (Week 7-8)
- [ ] Implement EchoEagle (overuse detection)
- [ ] Implement PatternPanther (spaCy integration for structure analysis)
- [ ] Implement PronunciationPenguin (Whisper confidence analysis)
- [ ] Implement EmpathyElephant (affective monitoring)
- [ ] Test listener signal quality with real conversations

### Phase 2.2: Content & Memory (Week 8-9)
- [ ] Implement ScriptSpider (actor clip indexing)
- [ ] Implement StoryStork (topic history)
- [ ] Implement CrawlerCrab (web content fetcher)
- [ ] Create actor clip import tool
- [ ] Build initial actor clip library (5-10 clips)

### Phase 2.3: Advanced Coaching (Week 9-10)
- [ ] Implement ActorAlbatross (shadowing drills)
- [ ] Implement ComprehensionCougar (listening exercises)
- [ ] Implement StrategySwan (learning strategies)
- [ ] Extend TaskTiger with 5 new drill types
- [ ] Test drill delivery end-to-end

### Phase 2.4: Orchestration Enhancements (Week 10-11)
- [ ] Extend OrchestratorOctopus with affective awareness
- [ ] Extend FocusFalcon with weekly themes
- [ ] Extend BoundaryBison with check-ins and dynamic intensity
- [ ] Test enhanced orchestration with all 21 agents

### Phase 2.5: Integration & Testing (Week 11-12)
- [ ] Full system integration (all agents active)
- [ ] Performance profiling (memory, latency)
- [ ] SSD write monitoring (should still be <200MB/day)
- [ ] User acceptance testing (multi-week trial)
- [ ] Documentation updates

---

## 8. Resource Allocation Updates

### Memory Budget (11GB total usable)
- **Phase 1 base:** ~8.4GB
- **Phase 2 additions:**
  - spaCy model (PatternPanther): ~500MB
  - Actor clip cache: ~100MB (streaming from SSD)
  - Topic history: ~50MB
  - Extended orchestrator buffers: ~100MB
- **Total estimated:** ~9.15GB (leaves 1.85GB headroom)

### SSD Storage
- Actor clips: ~1-2GB (one-time storage)
- Topic history: ~50MB (grows slowly)
- Phase 2 logs: +500KB/day (still under 50MB/day total)

### Latency Impact
- PatternPanther (spaCy): +300ms
- PronunciationPenguin: +200ms
- Other new listeners: +100ms
- **Total per utterance:** ~11.3s (still acceptable)

---

## 9. Configuration (.env additions for Phase 2)

```bash
# Phase 2 Listeners
ECHO_EAGLE_OVERUSE_THRESHOLD=2.0  # 2x normal frequency
PATTERN_PANTHER_SPACY_MODEL=en_core_web_sm
PRONUNCIATION_CONFIDENCE_THRESHOLD=0.6
EMPATHY_DRILL_SKIP_THRESHOLD=0.5  # 50% skip rate

# Content Sources
ACTOR_CLIP_DIRECTORY=media/actors
CRAWLER_YOUTUBE_DL_PATH=/usr/bin/yt-dlp
CRAWLER_CACHE_DIRECTORY=data/topics/cache

# Advanced Coaching
ACTOR_SHADOWING_ENABLED=true
LISTENING_COMPREHENSION_ENABLED=true
STRATEGY_MOMENTS_FREQUENCY=0.1  # 10% of sessions

# Weekly Themes
FOCUS_FALCON_WEEKLY_MODE=true
BOUNDARY_BISON_CHECKIN_DAY=monday
```

---

## 10. Migration from Phase 1

### Backward Compatibility
- All Phase 2 agents are **additive** (no breaking changes)
- Phase 2 can be disabled via feature flags:
  ```bash
  ZOO_PHASE2_ENABLED=false
  ```
- Users can enable agents incrementally:
  ```bash
  ZOO_ENABLE_ECHO_EAGLE=true
  ZOO_ENABLE_ACTOR_ALBATROSS=false  # Not ready yet
  ```

### Gradual Rollout
1. **Week 7-8:** Enable listeners (EchoEagle, PatternPanther) → observe signal quality
2. **Week 9:** Enable ScriptSpider + ActorAlbatross → test shadowing drills
3. **Week 10:** Enable full Phase 2 → monitor performance
4. **Week 11-12:** Tune and stabilize

---

## 11. Success Metrics

### Phase 2 Completion Criteria
- [ ] All 10 new agents implemented and tested
- [ ] Actor clip library (20+ clips indexed)
- [ ] Shadowing drills working end-to-end
- [ ] Listening comprehension exercises functional
- [ ] Affective monitoring adjusting intensity correctly
- [ ] Memory usage < 9.5GB during full sessions
- [ ] Average latency < 12s (with all agents active)

### Quality Metrics
- Pronunciation detection accuracy > 70%
- Overuse detection precision > 85%
- Shadowing drill completion rate > 40%
- Affective state detection accuracy > 75% (validated against user feedback)
- User satisfaction rating > 4.5/5

---

## 12. Advanced Features (Phase 2B+)

### Potential Future Extensions
1. **Forced Alignment for Pronunciation:**
   - Montreal Forced Aligner integration
   - Phoneme-level stress analysis

2. **Prosody Analysis:**
   - Pitch contour comparison (user vs actor)
   - Energy/intensity matching

3. **Multi-modal Input:**
   - Video clips (visual context for communication)
   - Body language cues (future: camera integration)

4. **Collaborative Learning:**
   - Compare progress with other users (anonymized)
   - Community-sourced actor clip library

5. **Adaptive SRS:**
   - ML-based interval prediction (vs fixed SM-2)
   - Personalized forgetting curves

---

## 13. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| spaCy memory overhead | Memory overflow | Use `en_core_web_sm`, disable if >500MB |
| Actor clips licensing | Legal issues | User-provided clips only, fair use for personal learning |
| Pronunciation false positives | Bad drills | Require 3+ misrecognitions before flagging |
| Too many drill types overwhelm | Analysis paralysis | FocusFalcon enforces single weekly theme |
| Web scraping rate limits | CrawlerCrab failures | Aggressive caching, manual fallback |
| Affective detection inaccurate | Wrong intensity adjustments | Conservative thresholds, user override available |

---

## Next Steps After Epic 1 Complete

1. **Stabilize Epic 1** - 2 weeks of real-world testing, bug fixes
2. **Gather user feedback** - Which features most requested?
3. **Prioritize Phase 2 features** - Adjust plan based on Epic 1 learnings
4. **Start Phase 2.1** - Advanced listeners first (lower risk)
5. **Iterate and refine** - Continuous improvement based on usage data

**Estimated Epic 2 completion:** 6 weeks (after Epic 1 stable)

**Total project timeline:** 12-14 weeks from start to full Phase 2 deployment
