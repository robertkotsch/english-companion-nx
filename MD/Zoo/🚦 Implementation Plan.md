# 🚦 Implementation Plan

## EPIC 1 vs EPIC 2

Now let’s split this into **what you build first** vs **what comes later**.

### EPIC 1 – MVP: “Smart but lean” trainer on Jetson Orin

**Goal:** A *usable*, robust coach that:

- corrects grammar,
- reduces fillers,
- reuses your Notion vocabulary,
- gives simple drills,
- and doesn’t overwhelm you.

### Must-have in EPIC 1

**0️⃣ Control & Taming**

- 🐙 **OrchestratorOctopus**

**1️⃣ Passive Listeners**

- 🦒 **GrammarGiraffe** – core grammar feedback
- 🦅 **FillerFalcon** – filler tracking
- 🐯 **TempoTiger** – basic WPM + pauses (even coarse is fine)
- 🐈‍⬛ **LexiLynx** – track vocab usage vs Notion
- (EchoEagle / PatternPanther / PronunciationPenguin / EmpathyElephant → EPIC 2)

**2️⃣ Knowledge & Memory**

- 🐦 **NotionNightingale** – at least *read-only* to start
- 🐿️ **SpacedSquirrel** – simple SRS (date-based, no full Anki logic needed at first)
- 🐼 **PersonaPanda** – minimal profile (C1 goal, accent preference, intensity mode)
- (ScriptSpider, StoryStork, CrawlerCrab → EPIC 2)

**3️⃣ Coaching & Intervention**

- 🐺 **CoachCoyote** – single LLM voice
- 🐯 **TaskTiger** – **limited drill set**, e.g.:
    - repeat without filler
    - repeat improved grammar version
    - use 1 Notion expression in a new sentence
- 🐕‍🦺 **SessionShepherd** – only:
    - quick session (5–7 min) vs full session (15–20 min)
- 🦅 **FocusFalcon** – very simple:
    - choose 1 main focus per session: *fillers* or *grammar* or *vocab*
- (ActorAlbatross, ComprehensionCougar, StrategySwan → EPIC 2)

**4️⃣ Day & Flow Control**

- 🐬 **DayDolphin** – minimal state machine (DAY_BOOT, WAITING, IN_SESSION, FREE_CONVERSATION, DAY_OVER)
- 🐦 **ScribeSparrow** – log sessions and progress basics
- 🦬 **BoundaryBison** – at least a simple **mode flag**:
    - `coach_mode = off | soft | normal`

---

### EPIC 2 – Extensions: “Full-blown excellent coach”

**Goal:** Add depth: actors, listening, pronunciation, motivation, strategies, richer context.

### Add in EPIC 2

**1️⃣ Passive Listeners**

- 🦅 **EchoEagle** – overuse patterns (“actually”, “kind of”, “a lot”)
- 🐆 **PatternPanther** – recurrent structures & error types
- 🐧 **PronunciationPenguin** – pronunciation & stress issues
- 🐘 **EmpathyElephant** – affective state (skipped drills, frustration language)

**2️⃣ Knowledge & Memory**

- 🕷️ **ScriptSpider** – structured clip store for actors + listening
- 🕊️ **StoryStork** – topic history (e-learning, 3D, leadership)
- 🦀 **CrawlerCrab** – web & social content fetcher (for actors, real topics)

**3️⃣ Coaching & Intervention**

- 🕊️ **ActorAlbatross** – actor shadowing, phrase mining
- 🐆 **ComprehensionCougar** – listening/gist exercises
- 🦢 **StrategySwan** – explicit learning strategies (paraphrasing, chunking etc.)
- Extend **TaskTiger** – more drill types (pronunciation, listening, strategies)
- Extend **FocusFalcon** – weekly themes (e.g. “adjectives”, “register switching”)

**4️⃣ Day & Flow Control**

- 🦬 **BoundaryBison** – richer:
    - weekly check-ins (upcoming meetings, personal priorities),
    - dynamic adjustment of intensity based on EmpathyElephant’s signals.