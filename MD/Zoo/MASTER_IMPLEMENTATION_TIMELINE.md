# Zoo System - Master Implementation Timeline

**Project:** English Companion NX - Zoo Agent System
**Duration:** 20 weeks (5 months)
**Target Hardware:** Jetson Orin NX 16GB
**Start Date:** TBD (assumes ~10-15 hours/week)

---

## Executive Summary

| Epic | Scope | Duration | Dependencies | Deliverables |
|------|-------|----------|--------------|--------------|
| **Epic 1** | MVP - Core agents | 6 weeks | Phase 2B voice assistant | 15 agents, signal system, orchestration |
| **Epic 1.5** | Core dashboards | 3 weeks | Epic 1 complete | 4 dashboards, web UI, API |
| **Epic 2** | Advanced agents | 6 weeks | Epic 1 stable | 10 agents, actors, listening, strategies |
| **Epic 3** | Advanced dashboards | 5 weeks | Epic 2 complete | 5 dashboards, skill radar, analytics |
| **Total** | Full system | **20 weeks** | - | 25 agents + 9 dashboards |

---

## Visual Timeline Overview

```
Week:  1   2   3   4   5   6   7   8   9   10  11  12  13  14  15  16  17  18  19  20
       |---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
Epic 1 [████████████████████████]
                                 ├─Stabilization─┤
Epic 1.5                         [████████████████]
                                                   ├─Testing─┤
Epic 2                                             [████████████████████████]
                                                                             ├─Stabilization─┤
Epic 3                                                                       [████████████████████]
       |---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
       W1  W2  W3  W4  W5  W6  W7  W8  W9  W10 W11 W12 W13 W14 W15 W16 W17 W18 W19 W20

Milestones:
   ▼ W6:  Epic 1 Complete (MVP working)
         ▼ W9:  Core Dashboards Live
               ▼ W10: Epic 2 Start (actors, pronunciation)
                           ▼ W15: Epic 2 Complete (all 25 agents)
                                     ▼ W20: Full System Complete
```

---

## Phase-by-Phase Breakdown

### EPIC 1: MVP Core Agents (Weeks 1-6)

#### Week 1: Foundation
```
Days 1-7 [██████████] Foundation
  ├─ Day 1-2:   Project structure setup (src/zoo/, directories)
  ├─ Day 2-3:   Signal system (signals.py, dataclasses)
  ├─ Day 3-4:   BaseListener abstract class
  ├─ Day 4-5:   DayDolphin state machine
  ├─ Day 5-6:   PersonaPanda (profile loader)
  └─ Day 7:     Unit tests + documentation

Deliverables: ✓ Zoo structure, ✓ Signal protocol, ✓ State machine
```

#### Week 2: Listeners (Part 1)
```
Days 8-14 [██████████] Passive Listeners
  ├─ Day 8-9:   FillerFalcon (regex-based, simple)
  ├─ Day 9-11:  GrammarGiraffe (LLM-based, complex)
  ├─ Day 11-12: TempoTiger (basic WPM + pauses)
  ├─ Day 12-13: LexiLynx (vocab matching)
  └─ Day 14:    Integration tests (all 4 listeners)

Deliverables: ✓ 4 listeners operational, ✓ Signal emission tested
```

#### Week 3: Memory & Planning
```
Days 15-21 [██████████] Knowledge Agents
  ├─ Day 15-16: NotionNightingale (read-only sync)
  ├─ Day 17-18: SpacedSquirrel (simple SRS)
  ├─ Day 18-19: SessionShepherd (daily planner)
  ├─ Day 19-20: FocusFalcon (focus selector)
  └─ Day 21:    Notion integration test (end-to-end)

Deliverables: ✓ Notion sync, ✓ SRS working, ✓ Session planning
```

#### Week 4: Orchestration
```
Days 22-28 [██████████] Core Orchestration
  ├─ Day 22-24: OrchestratorOctopus (signal processing)
  ├─ Day 24-25: Prioritization logic (scoring, filtering)
  ├─ Day 25-26: Drill-now vs buffer decisions
  ├─ Day 26-27: Mock signal testing (synthetic data)
  └─ Day 28:    Orchestrator integration tests

Deliverables: ✓ Orchestration working, ✓ Signal routing tested
```

#### Week 5: Coaching & Flow
```
Days 29-35 [██████████] Coaching + Logging
  ├─ Day 29-30: TaskTiger (3 drill types)
  ├─ Day 30-32: CoachCoyote (LLM integration)
  ├─ Day 32-33: ScribeSparrow (logging system)
  ├─ Day 33-34: BoundaryBison (mode control)
  └─ Day 35:    Full session flow test (boot→session→end)

Deliverables: ✓ Drills working, ✓ Logging operational
```

#### Week 6: Integration & Testing
```
Days 36-42 [██████████] Phase 2B Integration
  ├─ Day 36-37: Create voice_assistant_zoo.py
  ├─ Day 37-38: Integrate Zoo pipeline (Whisper→Zoo→Ollama)
  ├─ Day 38-39: End-to-end testing (wake→record→Zoo→TTS)
  ├─ Day 39-40: Memory profiling (<9GB target)
  ├─ Day 40-41: Performance tuning (latency optimization)
  └─ Day 42:    User acceptance test (real 15-min session)

Deliverables: ✓ Epic 1 Complete, ✓ MVP operational
Risk Buffer: +3 days (Week 7 start)
```

**Epic 1 Milestone:** ✅ 15 agents, working MVP, integrated with Phase 2B

---

### Stabilization Period (Week 7)

```
Days 43-49 [░░░░░░░░░░] Stabilization & Bug Fixes
  ├─ Real-world testing (daily sessions)
  ├─ Bug fixes and tuning
  ├─ Performance monitoring
  ├─ Documentation completion
  └─ Prepare for Epic 1.5

Critical: Do NOT start Epic 1.5 without stable Epic 1!
```

---

### EPIC 1.5: Core Dashboards (Weeks 8-9)

#### Week 8: Backend + API
```
Days 50-56 [██████████] Dashboard Backend
  ├─ Day 50-51: DataAggregator (log reading)
  ├─ Day 51-52: StatisticsCalculator (metrics)
  ├─ Day 52-53: FastAPI setup + health endpoint
  ├─ Day 53-54: /api/consistency/* endpoints
  ├─ Day 54-55: /api/grammar-fillers/* + /api/vocabulary/*
  ├─ Day 55-56: /api/session/last endpoint
  └─ Day 56:    API testing (Swagger docs)

Deliverables: ✓ Backend complete, ✓ All APIs working
```

#### Week 9: Frontend + Deployment
```
Days 57-63 [██████████] Web UI + Launch
  ├─ Day 57-58: HTML/CSS layout + Chart.js setup
  ├─ Day 58-59: Dashboard 1 & 2 (Consistency, Grammar)
  ├─ Day 59-60: Dashboard 3 & 4 (Vocabulary, Session)
  ├─ Day 60-61: Terminal dashboard (Rich UI)
  ├─ Day 61-62: systemd service setup
  └─ Day 63:    End-to-end dashboard testing

Deliverables: ✓ 4 dashboards live, ✓ Web UI accessible
```

**Week 10: Dashboard Testing**
```
Days 64-70 [░░░░░░░░░░] Testing & Polish
  ├─ User acceptance (view after real sessions)
  ├─ Mobile responsiveness check
  ├─ Performance tuning (<200ms API)
  └─ Documentation (DASHBOARD_GUIDE.md)
```

**Epic 1.5 Milestone:** ✅ 4 dashboards operational, web UI at http://jetson:8080

---

### EPIC 2: Advanced Agents (Weeks 11-15)

#### Week 11: Advanced Listeners
```
Days 71-77 [██████████] Phase 2 Listeners
  ├─ Day 71-72: EchoEagle (overuse detection)
  ├─ Day 72-74: PatternPanther (spaCy integration)
  ├─ Day 74-75: PronunciationPenguin (Whisper confidence)
  ├─ Day 75-76: EmpathyElephant (affective monitoring)
  └─ Day 77:    Listener integration tests

Deliverables: ✓ 4 new listeners, ✓ Signal quality validated
```

#### Week 12: Content & Memory
```
Days 78-84 [██████████] Content Agents
  ├─ Day 78-79: ScriptSpider (actor clip indexing)
  ├─ Day 79-80: StoryStork (topic history)
  ├─ Day 80-81: CrawlerCrab (web content fetcher)
  ├─ Day 81-82: Actor clip import tool
  ├─ Day 82-83: Build initial actor library (10 clips)
  └─ Day 84:    Content system tests

Deliverables: ✓ Actor library, ✓ Topic tracking, ✓ Content pipeline
```

#### Week 13: Advanced Coaching
```
Days 85-91 [██████████] Coaching Extensions
  ├─ Day 85-86: ActorAlbatross (shadowing drills)
  ├─ Day 86-88: ComprehensionCougar (listening exercises)
  ├─ Day 88-89: StrategySwan (learning strategies)
  ├─ Day 89-90: Extend TaskTiger (+5 drill types)
  └─ Day 91:    Coaching integration tests

Deliverables: ✓ 3 coaching agents, ✓ 8+ drill types total
```

#### Week 14: Orchestration Extensions
```
Days 92-98 [██████████] Enhanced Orchestration
  ├─ Day 92-93: Extend OrchestratorOctopus (affective awareness)
  ├─ Day 93-94: Extend FocusFalcon (weekly themes)
  ├─ Day 94-95: Extend BoundaryBison (check-ins, dynamic intensity)
  ├─ Day 95-96: Full system integration (all 25 agents)
  ├─ Day 96-97: Integration testing (complex scenarios)
  └─ Day 98:    Performance profiling (memory, latency)

Deliverables: ✓ Enhanced orchestration, ✓ All agents integrated
```

#### Week 15: Epic 2 Completion
```
Days 99-105 [██████████] Testing & Tuning
  ├─ Day 99-100:  End-to-end system tests
  ├─ Day 100-101: Memory optimization (<9.5GB target)
  ├─ Day 101-102: SSD write monitoring (<200MB/day)
  ├─ Day 102-103: Latency tuning (<12s per utterance)
  ├─ Day 103-104: User acceptance (multi-week trial)
  └─ Day 105:     Documentation updates

Deliverables: ✓ Epic 2 Complete, ✓ 25 agents operational
Risk Buffer: +3 days (Week 16 start)
```

**Epic 2 Milestone:** ✅ 10 new agents, actors, listening, strategies working

---

### Stabilization Period (Week 16)

```
Days 106-112 [░░░░░░░░░░] Epic 2 Stabilization
  ├─ Real-world testing (full feature set)
  ├─ Actor library expansion (20+ clips)
  ├─ Strategy effectiveness validation
  ├─ Bug fixes and tuning
  └─ Prepare for Epic 3
```

---

### EPIC 3: Advanced Dashboards (Weeks 17-20)

#### Week 17: Backend Analytics
```
Days 113-119 [██████████] Analytics Engine
  ├─ Day 113-114: Extend DataAggregator (Phase 2 signals)
  ├─ Day 114-115: SkillProfiler (multi-dimensional calculations)
  ├─ Day 115-116: TrendAnalyzer (time-series analytics)
  ├─ Day 116-117: PronunciationAnalyzer
  ├─ Day 117-118: AffectiveAnalyzer
  └─ Day 119:     Analytics unit tests

Deliverables: ✓ Analytics engine, ✓ Skill calculations
```

#### Week 18: API Extensions
```
Days 120-126 [██████████] Phase 3 APIs
  ├─ Day 120-121: /api/skill-radar/* endpoints
  ├─ Day 121-122: /api/pronunciation/* endpoints
  ├─ Day 122-123: /api/listening-actors/* endpoints
  ├─ Day 123-124: /api/emotion-load/* endpoints
  ├─ Day 124-125: /api/strategies/* endpoints
  └─ Day 126:     API testing + documentation

Deliverables: ✓ 5 new API endpoint groups
```

#### Week 19: Advanced Dashboards UI
```
Days 127-133 [██████████] Web UI Development
  ├─ Day 127-128: Skill Radar dashboard (radar chart)
  ├─ Day 128-129: Pronunciation dashboard
  ├─ Day 129-130: Listening & Actors dashboard
  ├─ Day 130-131: Emotion & Load dashboard
  ├─ Day 131-132: Strategies dashboard
  └─ Day 133:     Responsive design (all dashboards)

Deliverables: ✓ 5 advanced dashboards, ✓ Radar charts
```

#### Week 20: Final Integration
```
Days 134-140 [██████████] System Completion
  ├─ Day 134-135: Terminal UI extensions (Phase 3)
  ├─ Day 135-136: End-to-end testing (full dashboard suite)
  ├─ Day 136-137: Performance profiling (<350MB dashboard RAM)
  ├─ Day 137-138: User acceptance (all dashboards)
  ├─ Day 138-139: Final documentation (guides, API docs)
  └─ Day 140:     🎉 FULL SYSTEM LAUNCH 🎉

Deliverables: ✓ Epic 3 Complete, ✓ 9 total dashboards
```

**Epic 3 Milestone:** ✅ Complete Zoo System - 25 agents + 9 dashboards

---

## Critical Path Analysis

### Must-Finish-Before Dependencies

```
Epic 1 Foundation (W1)
  └─> Epic 1 Listeners (W2)
       └─> Epic 1 Memory (W3)
            └─> Epic 1 Orchestration (W4)
                 └─> Epic 1 Coaching (W5)
                      └─> Epic 1 Integration (W6)
                           └─> Stabilization (W7)
                                └─> Epic 1.5 Backend (W8)
                                     └─> Epic 1.5 Frontend (W9)
                                          └─> Epic 2 Start (W11)
                                               └─> [Epic 2 phases...]
                                                    └─> Epic 3 Start (W17)

⚠️ Critical Path: Epic 1 → Epic 1.5 → Epic 2 → Epic 3 (sequential)
```

### Parallel Work Opportunities

**Within Epic 1:**
- Week 2: Listeners can be developed partially in parallel (FillerFalcon + TempoTiger)
- Week 3: NotionNightingale + SpacedSquirrel independent
- Week 5: TaskTiger + ScribeSparrow can develop concurrently

**Within Epic 2:**
- Week 11: All 4 listeners can be developed in parallel (if multi-tasking)
- Week 12: ScriptSpider + StoryStork independent

**Within Epic 3:**
- Week 19: All 5 dashboards can be built in parallel (if multi-tasking)

---

## Resource Allocation Timeline

### Memory Budget Progression

```
Week 1-6:   Phase 2B base (8GB) → Epic 1 (8.4GB)   [+400MB]
Week 8-9:   Epic 1.5 dashboards                    [+160MB → 8.56GB total]
Week 11-15: Epic 2 agents                          [+750MB → 9.31GB total]
Week 17-20: Epic 3 dashboards                      [+150MB → 9.46GB total]

Headroom: 11GB available - 9.46GB used = 1.54GB buffer ✓
```

### Development Time Budget

```
Assuming 10-15 hours/week development time:

Low estimate (10h/week):   20 weeks × 10h = 200 hours total
Mid estimate (12.5h/week): 20 weeks × 12.5h = 250 hours total
High estimate (15h/week):  20 weeks × 15h = 300 hours total

Recommended: 12-15 hours/week for comfortable pace
```

---

## Milestone Checklist

### ✓ Week 6: Epic 1 Complete (MVP)
- [ ] All 15 agents implemented
- [ ] Signal system working
- [ ] Orchestration operational
- [ ] Integrated with Phase 2B
- [ ] Memory usage <9GB
- [ ] 15-min real session successful

### ✓ Week 9: Epic 1.5 Complete (Core Dashboards)
- [ ] All 4 dashboards live
- [ ] Web UI accessible (http://jetson:8080)
- [ ] API response times <200ms
- [ ] Terminal fallback working
- [ ] systemd service auto-start

### ✓ Week 15: Epic 2 Complete (Advanced Agents)
- [ ] 10 new agents operational
- [ ] Actor library (20+ clips)
- [ ] Listening comprehension working
- [ ] Pronunciation tracking functional
- [ ] Affective monitoring active
- [ ] Memory usage <9.5GB

### ✓ Week 20: Epic 3 Complete (Full System)
- [ ] 5 advanced dashboards live
- [ ] Skill radar visualization working
- [ ] Before/after examples displayed
- [ ] All 25 agents + 9 dashboards operational
- [ ] Memory usage <10GB
- [ ] Complete documentation

---

## Risk Management & Buffers

### Built-in Buffer Zones

| After Phase | Buffer Days | Purpose |
|-------------|-------------|---------|
| Epic 1 (W6) | +3 days (W7 start) | Bug fixes, performance tuning |
| Epic 1.5 (W9) | +1 week (W10) | Dashboard polish, user feedback |
| Epic 2 (W15) | +3 days (W16 start) | Stabilization, library expansion |
| Epic 3 (W20) | None (end of project) | Final delivery |

### Contingency Plans

**If Epic 1 runs over (>6 weeks):**
- Reduce Epic 1.5 scope: Build only dashboards 1-2, defer 3-4 to post-Epic 2
- Accept delay: Push entire timeline by 1 week

**If Epic 2 runs over (>6 weeks):**
- Defer Epic 3 entirely: Ship with core dashboards only
- Prioritize: EmpathyElephant + ActorAlbatross critical, others optional

**If memory budget exceeded:**
- Disable least-used agents (feature flags)
- Use smaller spaCy model (PatternPanther)
- Reduce context window (CoachCoyote)

---

## Testing Windows

### Continuous Testing (Throughout)
- Unit tests: After each component (daily)
- Integration tests: End of each week
- Memory profiling: Weekly

### Major Testing Phases
- **Week 6:** Epic 1 full system test (2 days)
- **Week 9:** Dashboard user acceptance (1 day)
- **Week 15:** Epic 2 multi-week trial (3 days)
- **Week 20:** Final system validation (2 days)

---

## Documentation Milestones

| Week | Documentation Deliverable |
|------|---------------------------|
| W1 | Signal protocol spec |
| W3 | Agent API documentation |
| W6 | Epic 1 user guide (VOICE_ASSISTANT_ZOO_GUIDE.md) |
| W9 | Dashboard user guide (DASHBOARD_GUIDE.md) |
| W15 | Epic 2 feature guide (actor library, strategies) |
| W20 | Complete system documentation |

---

## Success Criteria by Epic

### Epic 1 Success =
✓ 15-min conversation session works end-to-end
✓ GrammarGiraffe detects errors accurately (>80%)
✓ FillerFalcon tracks fillers correctly (>95%)
✓ Notion vocab synced and tracked
✓ Drills delivered naturally in conversation

### Epic 1.5 Success =
✓ Dashboards load <2s
✓ Charts display accurate data
✓ Session streaks calculated correctly
✓ Vocab usage stats match manual count

### Epic 2 Success =
✓ Actor shadowing drills work smoothly
✓ Pronunciation issues detected (>70% accuracy)
✓ EmpathyElephant adjusts intensity when needed
✓ Learning strategies delivered appropriately

### Epic 3 Success =
✓ Skill radar shows meaningful profile
✓ Before/after examples motivate user
✓ Pronunciation trends visible over time
✓ Emotion dashboard actionable

---

## Post-Launch Roadmap (Beyond Week 20)

### Month 6+: Optimization & Expansion
- Actor library growth (50+ clips)
- Fine-tune skill calculations based on usage
- Export features (PDF reports, CSV data)
- Mobile app (optional)
- Multi-user support (optional)

### Long-term Vision
- ML-based adaptive SRS
- Forced alignment for pronunciation
- Community actor library
- Integration with external platforms (Duolingo, Anki)

---

## Quick Reference: Week-by-Week Deliverables

```
W1:  Foundation (signals, state machine, profile)
W2:  4 Listeners (grammar, fillers, tempo, vocab)
W3:  Memory agents (Notion, SRS, planner)
W4:  Orchestration (signal routing, prioritization)
W5:  Coaching (drills, LLM coach, logging)
W6:  Integration + MVP COMPLETE
W7:  Stabilization buffer
W8:  Dashboard backend (API, aggregator)
W9:  Dashboard frontend + CORE DASHBOARDS LIVE
W10: Dashboard testing buffer
W11: Advanced listeners (4 new)
W12: Content agents (actors, topics, crawler)
W13: Advanced coaching (shadowing, listening, strategies)
W14: Extended orchestration (affective, weekly themes)
W15: Epic 2 testing + ADVANCED AGENTS COMPLETE
W16: Stabilization buffer
W17: Analytics engine (skill profiler, trends)
W18: Phase 3 APIs (5 endpoint groups)
W19: Advanced dashboards (5 new)
W20: Final integration + 🎉 FULL SYSTEM COMPLETE
```

---

**Total Duration:** 20 weeks (140 days)
**Total Effort:** 200-300 hours
**Deliverables:** 25 agents + 9 dashboards + Full documentation
**End State:** Production-ready AI conversation coach running 24/7 on Jetson Orin NX

**Last Updated:** 2024-12-15
**Status:** Planning Complete - Ready for Implementation
