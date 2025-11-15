# 🧬 Zoo v1.0 – Final Agent Set

### 0️⃣ Control & Taming

| Name | Role | What it does |
| --- | --- | --- |
| **OrchestratorOctopus** 🐙 | Zookeeper | Collects all signals from the zoo, decides *what* gets handled, *when*, and *how* (real-time vs later, which drill, which focus). |

---

### 1️⃣ Passive “Listener” Agents (always observing you)

| Name | Role | What it does |
| --- | --- | --- |
| **GrammarGiraffe** 🦒 | Grammar Sentry | Spots grammar mistakes and classifies them (articles, tense, word order…). |
| **FillerFalcon** 🦅 | Filler Radar | Tracks *uhm, uh, like, you know…* and computes filler rate. |
| **EchoEagle** 🦅 | Overuse Monitor | Detects overused words/phrases (*actually, basically, a lot, in this case*). |
| **PatternPanther** 🐆 | Sentence Pattern Profiler | Sees recurring sentence frames and German↔English transfer patterns. |
| **TempoTiger** 🐯 | Timing & Flow Monitor | Measures WPM, pause lengths, silent vs filled pauses, “stuck” pauses. |
| **LexiLynx** 🐈‍⬛ | Vocabulary Usage Tracker | Logs which target words/phrases you hear, attempt, and use correctly. |
| **PronunciationPenguin** 🐧 | Pronunciation & Stress Monitor | Spots often-misheard words and stress/prosody issues; flags them for pronunciation drills. |
| **EmpathyElephant** 🐘 | Affective & Motivation Monitor | Watches skipped drills, very short answers, self-critical language; flags low energy/frustration. |

---

### 2️⃣ Knowledge & Memory Agents (back-end brain)

| Name | Role | What it does |
| --- | --- | --- |
| **NotionNightingale** 🐦 | Vocabulary Librarian | Syncs your Notion vocab DB with local vocab tables (read/write). |
| **SpacedSquirrel** 🐿️ | Repetition Scheduler | Runs spaced repetition; decides what needs review each day. |
| **ScriptSpider** 🕷️ | Actor Corpus Curator | Stores actor clips, transcripts, and mined expressions. |
| **PersonaPanda** 🐼 | User Profile & Goals Keeper | Keeps CEFR target, weekly focus, accent/actor preferences, coach intensity, topics. |
| **StoryStork** 🕊️ | Context & Topics Archive | Remembers past themes (e-learning, 3D, leadership) for future drills. |
| **CrawlerCrab** 🦀 | Fetching Web Content | Collects content from web/social platforms, hands it to ScriptSpider & StoryStork. |

---

### 3️⃣ Coaching & Intervention Agents (active coaches)

| Name | Role | What it does |
| --- | --- | --- |
| **CoachCoyote** 🐺 | Main Conversation Coach | Talks to you, integrates all signals, chooses tone and explanations. |
| **TaskTiger** 🐯 | Drill Designer | Turns weaknesses into concrete speaking/listening tasks. |
| **SessionShepherd** 🐕‍🦺 | Daily Workout & Session Planner | Builds today’s plan; picks blocks for quick vs full sessions. |
| **ActorAlbatross** 🕊️ | Actor Shadow Coach | Picks actor clips, runs shadowing, mines reusable phrases and feeds them in. |
| **FocusFalcon** 🦅 | Session Focus Selector | Chooses 1–3 key focus areas per session (e.g. fillers, phrasal verbs, adjectives). |
| **ComprehensionCougar** 🐆 | Listening & Gist Coach | Uses clips to run listening tasks: comprehension questions, gist, keyword dictation. |
| **StrategySwan** 🦢 | Learning Strategy Coach | Injects short “strategy moments” (paraphrasing, chunking, self-correction techniques). |

---

### 4️⃣ Day & Flow Control (meta-process)

| Name | Role | What it does |
| --- | --- | --- |
| **DayDolphin** 🐬 | Day State Manager | Manages states: `DAY_BOOT → WAITING → IN_SESSION → FREE_CONVERSATION → DAY_OVER`. |
| **ScribeSparrow** 🐦 | Session Logger | Logs which blocks were done, partial completions, and daily summaries. |
| **BoundaryBison** 🦬 | Mode & Check-in Manager | Manages coach intensity (off/soft/intense) and schedules regular goal check-ins. |

[🎻 Flow plan](🎻%20Flow%20plan.md)

[🚦 Implementation Plan](🚦%20Implementation%20Plan.md)