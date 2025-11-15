# Epic 3: Advanced Dashboards Implementation Plan

**Goal:** Add depth - Skill radar, pronunciation tracking, actor/listening progress, affective monitoring, and learning strategies visualization.

**Prerequisites:** Epic 2 (Extensions) complete with all Phase 2 agents operational.

**Timing:** Implement after Epic 2 stable, parallel with ongoing system use.

---

## 1. Architecture Overview

### Extended Dashboard Architecture
```
[Phase 1 + 2 Agents] → [ScribeSparrow Enhanced Logs] → [Dashboard API v2] → [Web UI]
                              ↓
                    [Advanced Aggregator]
                              ↓
                  [Multi-dimensional Analytics]
                              ↓
                    [Skill Profiler + Trend Analyzer]
```

### New Capabilities
- **Multi-dimensional skill profiling** (radar charts)
- **Pronunciation pattern tracking** (word-level analysis)
- **Actor library activity** (shadowing progress)
- **Affective state monitoring** (motivation trends)
- **Learning strategy adoption** (metacognitive awareness)

---

## 2. File Structure Additions

```
english-companion-nx/
├── src/
│   ├── dashboards/
│   │   ├── aggregator.py                # EXTENDED: Phase 2 data
│   │   ├── statistics.py                # EXTENDED: Advanced metrics
│   │   │
│   │   ├── routes/
│   │   │   ├── skill_radar.py          # NEW: Skill profile dashboard
│   │   │   ├── pronunciation.py         # NEW: Pronunciation dashboard
│   │   │   ├── listening_actors.py      # NEW: Listening & actors dashboard
│   │   │   ├── emotion_load.py          # NEW: Affective monitoring
│   │   │   └── strategies.py            # NEW: Learning strategies
│   │   │
│   │   ├── models/
│   │   │   ├── skill_profile.py        # NEW: Multi-dimensional skills
│   │   │   ├── pronunciation_stats.py  # NEW: Pronunciation metrics
│   │   │   ├── actor_stats.py          # NEW: Actor activity
│   │   │   └── strategy_stats.py       # NEW: Strategy usage
│   │   │
│   │   └── analytics/                   # NEW: Advanced analysis
│   │       ├── __init__.py
│   │       ├── skill_profiler.py       # Skill radar calculation
│   │       ├── trend_analyzer.py       # Time-series trends
│   │       └── comparison_engine.py    # Before/after comparisons
│   │
│   └── zoo/
│       └── flow/
│           └── scribe_sparrow.py       # EXTENDED: Phase 2 signal logging
│
├── web/
│   ├── static/
│   │   ├── js/
│   │   │   ├── skill_radar.js          # NEW: Radar chart logic
│   │   │   ├── pronunciation.js        # NEW: Pronunciation dashboard
│   │   │   ├── listening_actors.js     # NEW: Actor/listening dashboard
│   │   │   ├── emotion_load.js         # NEW: Affective dashboard
│   │   │   └── strategies.js           # NEW: Strategy dashboard
│   │   │
│   │   └── vendor/
│   │       └── chart-radarchart.min.js # Chart.js radar plugin
│   │
│   └── templates/
│       ├── skill_radar.html
│       ├── pronunciation.html
│       ├── listening_actors.html
│       ├── emotion_load.html
│       └── strategies.html
│
└── test_dashboards_phase3_*.py         # Phase 3 dashboard tests
```

---

## 3. New Dashboard Components

### 3.1 Dashboard: Skill Radar

**Purpose:** High-level multi-dimensional skill profile with progress tracking.

**API Endpoint:**
```
GET /api/skill-radar/profile?timeframe=current
Response: {
  "current": {
    "grammar_accuracy": 0.85,      // 0.0-1.0
    "lexical_variety": 0.72,       // 0.0-1.0
    "fluency": 0.68,               // 0.0-1.0
    "pronunciation": 0.75,         // 0.0-1.0
    "listening_comprehension": 0.80, // 0.0-1.0
    "strategy_use": 0.65           // 0.0-1.0
  },
  "30_days_ago": {
    "grammar_accuracy": 0.78,
    "lexical_variety": 0.68,
    "fluency": 0.62,
    "pronunciation": 0.70,
    "listening_comprehension": 0.75,
    "strategy_use": 0.55
  },
  "progress": {
    "grammar_accuracy": "+9%",
    "lexical_variety": "+6%",
    "fluency": "+10%",
    "pronunciation": "+7%",
    "listening_comprehension": "+7%",
    "strategy_use": "+18%"
  }
}
```

**Metric Calculations:**

**Grammar Accuracy:**
```python
def calculate_grammar_accuracy(signals: List[Signal]) -> float:
    total_words = sum(len(u.text.split()) for u in utterances)
    grammar_errors = len([s for s in signals if s.source == "GrammarGiraffe"])
    error_rate = grammar_errors / (total_words / 100)  # per 100 words
    accuracy = max(0, 1 - (error_rate / 10))  # 10 errors/100 words = 0.0 accuracy
    return accuracy
```

**Lexical Variety:**
```python
def calculate_lexical_variety(signals: List[Signal], utterances: List[Utterance]) -> float:
    overuse_signals = [s for s in signals if s.source == "EchoEagle"]
    overuse_penalty = len(overuse_signals) * 0.05

    # Type-token ratio (unique words / total words)
    all_words = " ".join(u.text for u in utterances).lower().split()
    unique_words = set(all_words)
    ttr = len(unique_words) / len(all_words) if all_words else 0

    variety_score = max(0, ttr - overuse_penalty)
    return min(1.0, variety_score * 1.5)  # Normalize to 0-1
```

**Fluency:**
```python
def calculate_fluency(signals: List[Signal]) -> float:
    tempo_signals = [s for s in signals if s.source == "TempoTiger"]
    filler_signals = [s for s in signals if s.source == "FillerFalcon"]

    avg_wpm = statistics.mean([s.data["wpm"] for s in tempo_signals])
    filler_rate = statistics.mean([s.data["filler_rate"] for s in filler_signals])

    # Ideal WPM: 130-150, filler rate < 5%
    wpm_score = 1 - abs(140 - avg_wpm) / 140
    filler_penalty = filler_rate / 100

    fluency = max(0, (wpm_score * 0.7 + (1 - filler_penalty) * 0.3))
    return fluency
```

**Pronunciation:**
```python
def calculate_pronunciation(signals: List[Signal]) -> float:
    pron_signals = [s for s in signals if s.source == "PronunciationPenguin"]
    total_words = sum(len(u.text.split()) for u in utterances)

    # Count unique mispronounced words (not repetitions)
    problem_words = set(s.data["word"] for s in pron_signals)
    error_rate = len(problem_words) / (total_words / 100)

    pronunciation_score = max(0, 1 - (error_rate / 5))  # 5 unique errors/100 words = 0.0
    return pronunciation_score
```

**Listening Comprehension:**
```python
def calculate_listening_comprehension(comprehension_results: List[ComprehensionResult]) -> float:
    if not comprehension_results:
        return 0.0

    scores = [r.score for r in comprehension_results]
    return statistics.mean(scores)
```

**Strategy Use:**
```python
def calculate_strategy_use(strategy_events: List[StrategyEvent]) -> float:
    total_drills = len(all_drills)
    strategy_drills = len([d for d in all_drills if d.type == "strategy"])

    if total_drills == 0:
        return 0.0

    # Successful strategy applications
    successful = len([e for e in strategy_events if e.success])
    success_rate = successful / len(strategy_events) if strategy_events else 0

    # Combination of frequency and success
    frequency_score = min(1.0, strategy_drills / total_drills * 3)
    return (frequency_score * 0.5 + success_rate * 0.5)
```

**Web Implementation (Chart.js Radar):**
```javascript
// web/static/js/skill_radar.js
async function loadSkillRadar() {
    const data = await fetch('/api/skill-radar/profile?timeframe=current').then(r => r.json());

    const ctx = document.getElementById('skillRadarChart').getContext('2d');
    new Chart(ctx, {
        type: 'radar',
        data: {
            labels: [
                'Grammar',
                'Vocabulary',
                'Fluency',
                'Pronunciation',
                'Listening',
                'Strategies'
            ],
            datasets: [
                {
                    label: 'Current',
                    data: [
                        data.current.grammar_accuracy,
                        data.current.lexical_variety,
                        data.current.fluency,
                        data.current.pronunciation,
                        data.current.listening_comprehension,
                        data.current.strategy_use
                    ],
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.2)'
                },
                {
                    label: '30 Days Ago',
                    data: [
                        data['30_days_ago'].grammar_accuracy,
                        data['30_days_ago'].lexical_variety,
                        data['30_days_ago'].fluency,
                        data['30_days_ago'].pronunciation,
                        data['30_days_ago'].listening_comprehension,
                        data['30_days_ago'].strategy_use
                    ],
                    borderColor: '#9ca3af',
                    backgroundColor: 'rgba(156, 163, 175, 0.1)',
                    borderDash: [5, 5]
                }
            ]
        },
        options: {
            scales: {
                r: {
                    min: 0,
                    max: 1,
                    ticks: { stepSize: 0.2 }
                }
            }
        }
    });
}
```

---

### 3.2 Dashboard: Pronunciation & Prosody

**Purpose:** Track pronunciation improvements and problem patterns.

**API Endpoint:**
```
GET /api/pronunciation/stats?days=28
Response: {
  "problem_words": [
    {
      "word": "comfortable",
      "misheard_count": 8,
      "trend": "↓",  // improving
      "phoneme_issue": "/r/ cluster",
      "last_occurrence": "2024-12-14"
    },
    {
      "word": "world",
      "misheard_count": 6,
      "trend": "→",  // stable
      "phoneme_issue": "/w/ vs /v/",
      "last_occurrence": "2024-12-15"
    }
  ],
  "shadowing_activity": {
    "lines_shadowed_this_week": 15,
    "acceptable_rhythm_percentage": 73,
    "actors_practiced": ["Denzel Washington", "Morgan Freeman"]
  },
  "chunking_patterns": {
    "avg_phrase_length_words": 4.2,
    "avg_pause_between_chunks_sec": 0.8,
    "improvement_vs_30d_ago": "+12%"
  }
}
```

**Implementation:**
```python
# src/dashboards/analytics/skill_profiler.py
class PronunciationAnalyzer:
    def analyze_problem_words(self, signals: List[Signal], days: int) -> List[ProblemWord]:
        pron_signals = [s for s in signals
                       if s.source == "PronunciationPenguin"
                       and s.timestamp > (now - timedelta(days=days))]

        # Group by word
        word_counts = defaultdict(list)
        for signal in pron_signals:
            word = signal.data["word"]
            word_counts[word].append(signal)

        problem_words = []
        for word, word_signals in word_counts.items():
            trend = self._calculate_trend(word_signals)
            problem_words.append(ProblemWord(
                word=word,
                misheard_count=len(word_signals),
                trend=trend,
                phoneme_issue=word_signals[0].data.get("phoneme_issue", "unknown"),
                last_occurrence=max(s.timestamp for s in word_signals)
            ))

        return sorted(problem_words, key=lambda w: w.misheard_count, reverse=True)

    def _calculate_trend(self, signals: List[Signal]) -> str:
        # Split into first half and second half
        mid = len(signals) // 2
        first_half = signals[:mid]
        second_half = signals[mid:]

        if not first_half or not second_half:
            return "→"

        first_avg = len(first_half) / (signals[-1].timestamp - signals[0].timestamp)
        second_avg = len(second_half) / (signals[-1].timestamp - signals[mid].timestamp)

        if second_avg < first_avg * 0.7:
            return "↓"  # Improving
        elif second_avg > first_avg * 1.3:
            return "↑"  # Worsening
        else:
            return "→"  # Stable
```

---

### 3.3 Dashboard: Listening & Actors

**Purpose:** Track listening comprehension progress and actor-based learning.

**API Endpoint:**
```
GET /api/listening-actors/stats?days=28
Response: {
  "listening_performance": {
    "comprehension_questions": {
      "attempted": 12,
      "correct": 9,
      "score": 0.75
    },
    "gist_summary": {
      "attempted": 8,
      "acceptable": 7,
      "score": 0.88
    },
    "keyword_dictation": {
      "attempted": 15,
      "correct": 11,
      "score": 0.73
    },
    "trend": "↑ +8% vs last month"
  },
  "actor_activity": {
    "actors_practiced": [
      {
        "name": "Denzel Washington",
        "clips_used": 8,
        "shadowing_sessions": 12,
        "favorite_phrases": [
          "gotta do what you gotta do",
          "not by the book"
        ]
      },
      {
        "name": "Morgan Freeman",
        "clips_used": 5,
        "shadowing_sessions": 7,
        "favorite_phrases": [
          "get busy living or get busy dying"
        ]
      }
    ]
  },
  "phrase_adoption": [
    {
      "phrase": "gotta do what you gotta do",
      "source": "Denzel Washington - The Equalizer",
      "times_used_spontaneously": 3,
      "last_used": "2024-12-14"
    }
  ]
}
```

**Visualization:**
- Table of listening task scores with trend sparklines
- Actor "trading cards" showing activity
- Timeline of phrase adoption (actor → your speech)

---

### 3.4 Dashboard: Emotion & Load

**Purpose:** Monitor affective state and adjust coaching intensity.

**API Endpoint:**
```
GET /api/emotion-load/stats?days=28
Response: {
  "drill_engagement": {
    "offered": 45,
    "completed": 32,
    "skipped": 13,
    "completion_rate": 0.71,
    "trend": "↓ -5% vs last week"
  },
  "self_talk_monitor": {
    "negative_count": 4,
    "examples": [
      "I can't get this right",
      "This is too hard for me"
    ],
    "trend": "→ stable"
  },
  "mode_usage": {
    "off": 0.1,      // 10% of time
    "soft": 0.3,     // 30%
    "normal": 0.55,  // 55%
    "intense": 0.05  // 5%
  },
  "recommendations": [
    "Drill skip rate increasing - consider reducing intensity",
    "Self-critical language detected - focus on wins"
  ]
}
```

**Implementation:**
```python
# src/dashboards/analytics/skill_profiler.py
class AffectiveAnalyzer:
    def analyze_drill_engagement(self, sessions: List[Session]) -> DrillEngagement:
        total_offered = sum(s.drills_offered for s in sessions)
        total_completed = sum(s.drills_completed for s in sessions)
        total_skipped = sum(s.drills_skipped for s in sessions)

        completion_rate = total_completed / total_offered if total_offered else 0

        # Trend: compare last week vs previous week
        last_week = [s for s in sessions if s.start_time > (now - timedelta(days=7))]
        prev_week = [s for s in sessions
                    if (now - timedelta(days=14)) < s.start_time <= (now - timedelta(days=7))]

        last_week_rate = sum(s.drills_completed for s in last_week) / sum(s.drills_offered for s in last_week)
        prev_week_rate = sum(s.drills_completed for s in prev_week) / sum(s.drills_offered for s in prev_week)

        trend_pct = ((last_week_rate - prev_week_rate) / prev_week_rate * 100) if prev_week_rate else 0
        trend = f"↓ {trend_pct:.0f}%" if trend_pct < -5 else f"↑ +{trend_pct:.0f}%" if trend_pct > 5 else "→ stable"

        return DrillEngagement(
            offered=total_offered,
            completed=total_completed,
            skipped=total_skipped,
            completion_rate=completion_rate,
            trend=trend
        )
```

**Visualization:**
- Stacked bar chart: completed vs skipped drills over time
- Word cloud of self-critical phrases (with counts)
- Pie chart: mode distribution

---

### 3.5 Dashboard: Strategic Learning

**Purpose:** Show metacognitive strategy usage and effectiveness.

**API Endpoint:**
```
GET /api/strategies/stats?days=28
Response: {
  "strategy_usage": {
    "paraphrasing": 12,
    "chunking": 8,
    "self_correction": 15,
    "shadowing_technique": 10,
    "vocabulary_anchoring": 6
  },
  "before_after_examples": [
    {
      "strategy": "paraphrasing",
      "before": "The system is very good and works well.",
      "after": "The platform performs reliably and delivers consistent results.",
      "date": "2024-12-10"
    },
    {
      "strategy": "chunking",
      "before": "Iwaswonderingifyoucouldhelpmewiththeprojectbecauseitsquitecomplicated",
      "after": "I was wondering / if you could help me / with the project / because it's quite complicated",
      "date": "2024-12-12"
    }
  ],
  "success_rate_by_strategy": {
    "paraphrasing": 0.83,
    "chunking": 0.75,
    "self_correction": 0.90,
    "shadowing_technique": 0.70,
    "vocabulary_anchoring": 0.67
  }
}
```

**Visualization:**
- Bar chart: strategy usage counts
- Table: before/after examples (highly motivating!)
- Heat map: success rate by strategy type

---

## 4. Advanced Analytics Engine

### Skill Profiler (`src/dashboards/analytics/skill_profiler.py`)

**Purpose:** Multi-dimensional skill calculation across all agents.

```python
class SkillProfiler:
    def __init__(self, aggregator: DataAggregator):
        self.aggregator = aggregator

    def calculate_skill_profile(self, start_date, end_date) -> SkillProfile:
        sessions = self.aggregator.get_sessions_by_date(start_date, end_date)
        signals = self._get_all_signals(sessions)
        utterances = self._get_all_utterances(sessions)

        return SkillProfile(
            grammar_accuracy=self._calc_grammar_accuracy(signals, utterances),
            lexical_variety=self._calc_lexical_variety(signals, utterances),
            fluency=self._calc_fluency(signals),
            pronunciation=self._calc_pronunciation(signals, utterances),
            listening_comprehension=self._calc_listening(sessions),
            strategy_use=self._calc_strategy_use(sessions)
        )

    def compare_profiles(self, profile1: SkillProfile, profile2: SkillProfile) -> ProfileComparison:
        # Calculate deltas and percentage changes
        pass
```

---

### Trend Analyzer (`src/dashboards/analytics/trend_analyzer.py`)

**Purpose:** Time-series analysis for all metrics.

```python
class TrendAnalyzer:
    def analyze_trend(self, data_points: List[DataPoint], window_days=7) -> Trend:
        # Moving average, regression, trend direction
        pass

    def detect_anomalies(self, data_points: List[DataPoint]) -> List[Anomaly]:
        # Statistical outlier detection
        pass

    def forecast_progress(self, historical_data: List[DataPoint], days_ahead=30) -> Forecast:
        # Simple linear extrapolation
        pass
```

---

## 5. Implementation Tasks

### Phase 3.1: Backend Extensions (Week 1-2)
- [ ] Extend DataAggregator for Phase 2 signals
- [ ] Implement SkillProfiler (multi-dimensional calculations)
- [ ] Implement TrendAnalyzer (time-series analytics)
- [ ] Implement PronunciationAnalyzer
- [ ] Implement AffectiveAnalyzer
- [ ] Unit tests for all analytics

### Phase 3.2: API Endpoints (Week 2-3)
- [ ] Implement `/api/skill-radar/*` endpoints
- [ ] Implement `/api/pronunciation/*` endpoints
- [ ] Implement `/api/listening-actors/*` endpoints
- [ ] Implement `/api/emotion-load/*` endpoints
- [ ] Implement `/api/strategies/*` endpoints
- [ ] API documentation updates

### Phase 3.3: Web Frontend (Week 3-4)
- [ ] Build Skill Radar dashboard (radar chart)
- [ ] Build Pronunciation dashboard
- [ ] Build Listening & Actors dashboard
- [ ] Build Emotion & Load dashboard
- [ ] Build Strategies dashboard
- [ ] Responsive design for all new dashboards

### Phase 3.4: Terminal Extensions (Week 4)
- [ ] Extend terminal UI for Phase 3 dashboards
- [ ] Add skill profile ASCII visualization
- [ ] Add strategy usage tables

### Phase 3.5: Integration & Testing (Week 4-5)
- [ ] End-to-end testing with Phase 2 data
- [ ] Performance profiling (ensure <200ms API responses)
- [ ] User acceptance testing
- [ ] Documentation updates

---

## 6. Resource Allocation

### Memory Budget
- **Analytics engine:** ~100MB (caching skill profiles)
- **Extended aggregator:** +50MB
- **Total Phase 3 overhead:** ~150MB
- **Combined with Phase 1.5:** ~310MB total dashboard memory

### SSD Usage
- **Analytics cache:** ~20MB (daily skill profiles)
- **Still read-only:** No additional writes

---

## 7. Configuration (.env additions)

```bash
# Phase 3 Dashboards
DASHBOARD_SKILL_RADAR_ENABLED=true
DASHBOARD_PRONUNCIATION_ENABLED=true
DASHBOARD_LISTENING_ACTORS_ENABLED=true
DASHBOARD_EMOTION_LOAD_ENABLED=true
DASHBOARD_STRATEGIES_ENABLED=true

# Analytics
SKILL_PROFILE_CACHE_DAYS=30
TREND_ANALYSIS_WINDOW_DAYS=7
PRONUNCIATION_MIN_OCCURRENCES=3
STRATEGY_SUCCESS_THRESHOLD=0.7
```

---

## 8. Success Metrics

### Completion Criteria
- [ ] All 5 advanced dashboards implemented
- [ ] Skill radar calculates correctly
- [ ] Pronunciation tracking operational
- [ ] Actor/listening stats accurate
- [ ] Affective monitoring functional
- [ ] Strategy visualization complete
- [ ] Memory usage <350MB total (dashboards)
- [ ] API response times <300ms

### Quality Metrics
- Skill profile accuracy: Validated against manual review
- Trend detection: Correctly identifies improving/declining skills
- User engagement: Advanced dashboards viewed weekly
- Actionable insights: Users adjust practice based on emotion/load data

---

## 9. Future Enhancements (Post Epic 3)

### Phase 3B (Optional)
- [ ] Export skill profiles to PDF reports
- [ ] Compare with other users (anonymized benchmarks)
- [ ] AI-generated insights: "You're improving fastest in..."
- [ ] Predictive coaching: "At this rate, you'll reach C1 in..."
- [ ] Integration with external tracking (Duolingo, Anki)

---

## Next Steps After Epic 2 Complete

1. **Stabilize Epic 2** - 2-4 weeks real-world testing
2. **Gather Phase 2 data** - Ensure rich signal diversity for analytics
3. **Start Phase 3.1** - Backend analytics engine
4. **Iterate based on feedback** - Adjust skill calculations if needed
5. **Deploy incrementally** - One dashboard at a time

**Estimated Epic 3 completion:** 5 weeks (after Epic 2 stable)

**Total dashboard project timeline:** 8 weeks (Phase 1.5 + Phase 3)
