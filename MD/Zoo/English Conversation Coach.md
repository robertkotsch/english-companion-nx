# English Conversation Coach

## 0️⃣ Control & Taming

| New Name | Role | What it does |
| --- | --- | --- |
| OrchestratorOctopus | Zookeeper | collects all signals from the zoo, decides *what* gets handled, *when*, and *how*. |

## 1️⃣ Passive “Listener” Agents (always observing you)

These don’t talk, they just watch and send signals.

| New Name | Role | What it does |
| --- | --- | --- |
| **GrammarGiraffe** | Grammar Sentry | Spots grammar mistakes and classifies them (articles, tense, word order…). |
| **FillerFalcon** | Filler Radar | Tracks *uh, um, you know, like…* and computes your filler rate. |
| **EchoEagle** | Overuse Monitor | Detects overused words/phrases (*actually, basically, a lot, in this case*). |
| **PatternPanther** | Sentence Pattern Profiler | Sees recurring sentence frames and German↔English transfer patterns. |
| **TempoTiger** | Timing & Flow Monitor | Measures WPM, pause lengths, silent vs filled pauses, long “stuck” pauses. |
| **LexiLynx** | Vocabulary Usage Tracker | Logs which target words/phrases you hear, attempt, and use correctly. |
| PronunciationPenguin  | Pronunciation & Stress Monitor | Watches STT output + confidence to spot often-misheard words, stress issues and prosody problems; sends signals for targeted pronunciation drills and shadowing. |
| EmpathyElephant  | Affective & Motivation Monitor | Watches patterns like skipped drills, very short answers, self-critical language (“I’m bad at this”), and flags low-energy or frustration states so CoachCoyote can adjust tone and SessionShepherd can lighten the plan. |

## 2️⃣ Knowledge & Memory Agents (back-end brain)

They organise vocab, repetition, actors, and your profile.

| New Name | Role | What it does |
| --- | --- | --- |
| **NotionNightingale** | Vocabulary Librarian | Syncs your Notion vocab DB with the local vocab tables. |
| **SpacedSquirrel** | Repetition Scheduler | Runs spaced repetition; decides what needs review on each day. |
| **ScriptSpider** | Actor Corpus Curator | Stores actor clips, transcripts, and mined expressions. |
| **PersonaPanda** | User Profile & Goals Keeper | Keeps CEFR target, weekly focus, accent/actor preferences, topics. |
| **StoryStork** (opt.) | Context & Topics Archive | Remembers past themes (e-learning, 3D, leadership) for future drills. |
| CrawlerCrab | Fetching Web Content | Collects content from the web and social platforms, then hands it over to ScriptSpider & friends |
| ComprehensionCougar  | Listening & Gist Coach | Uses clips from ScriptSpider (and actors) to run listening tasks: comprehension questions, “repeat the gist”, short dictations of key phrases. |

## 3️⃣ Coaching & Intervention Agents (active coaches)

These are the ones that *do* something with all the signals.

| New Name | Role | What it does |
| --- | --- | --- |
| **CoachCoyote** | Main Conversation Coach | Talks to you, integrates all other signals, chooses tone and explanations. |
| **TaskTiger** | Drill Designer | Turns weaknesses into concrete speaking tasks and exercises. |
| **SessionShepherd** | Daily Workout & Session Planner | Builds today’s plan; picks blocks for quick vs full sessions. |
| **ActorAlbatross** | Actor Shadow Coach | Picks actor clips, runs shadowing, mines reusable expressions and feeds them in. |
| **FocusFalcon** | Session Focus Selector | Chooses 1–3 key focus areas per session (e.g. fillers, phrasal verbs). |
| StrategySwan  | Learning Strategy Coach | Injects short “strategy moments” into sessions: explains techniques (paraphrasing when stuck, chunking long sentences, listening for keywords), and designs mini-tasks to practise them. |

## 4️⃣ Day & Flow Control (meta-process)

These manage “what state of the day/session we’re in”.

| New Name | Role | What it does |
| --- | --- | --- |
| **DayDolphin** | Day State Manager | Manages states: `DAY_BOOT → WAITING → IN_SESSION → FREE_CONVERSATION → DAY_OVER`. |
| **ScribeSparrow** | Session Logger | Logs which blocks were done, partial completions, and daily summaries. |
| BoundaryBison  | Mode & Check-in Manager | Manages coach intensity modes (off / soft / intense) and schedules regular goal check-ins; updates PersonaPanda with your preferences and upcoming key events. |

### One-glance overview 🧠

### Updated category overview with the 5 new aspects

- **0️⃣ Control & Taming**
    - OrchestratorOctopus
- **1️⃣ Passive Listeners**
    - GrammarGiraffe, FillerFalcon, EchoEagle, PatternPanther, TempoTiger, LexiLynx
    - **+ PronunciationPenguin, EmpathyElephant**
- **2️⃣ Knowledge & Memory**
    - NotionNightingale, SpacedSquirrel, ScriptSpider, PersonaPanda, StoryStork, CrawlerCrab
- **3️⃣ Coaching & Intervention**
    - CoachCoyote, TaskTiger, SessionShepherd, ActorAlbatross, FocusFalcon
    - **+ ComprehensionCougar, StrategySwan**
- **4️⃣ Day & Flow Control**
    - DayDolphin, ScribeSparrow
    - + BoundaryBison

## Example: one utterance, many animals, one action

You say:

> Uhm, I don’t really know, actually, but, uhm, it can be that the process is kind of confusing for the most of the people.
> 

Signals:

- **FillerFalcon** → `filler_overuse` severity 0.9
- **EchoEagle** → `overused_word` = “actually”, “kind of”
- **GrammarGiraffe** → minor `article` issue (“for the most of the people”)
- **PatternPanther** → repetitive hedge pattern (“I don’t really know / it can be that”)
- **TempoTiger** → WPM fine, pause distribution okay → no strong signal

OrchestratorOctopus:

1. Scores all signals. Suppose today’s focus is *fillers* (FocusFalcon), so filler signal gets priority.
2. Pushes **only the filler signal** into the real-time queue.
3. Sends a task request to **TaskTiger**:
    
    > “Design a micro-drill: repeat last sentence with fewer fillers.”
    > 
4. CoachCoyote says:
    
    > “There were quite a few fillers in that sentence. Try it again using only one short pause and no uhm / kind of / actually.”
    > 

All other issues:

- article slip → stored in session buffer → maybe used in the end-of-session recap
- overused “actually” → maybe becomes part of a later 3-sentence drill
- hedge pattern → goes into long-term stats

So: many eyes watching you, **one calm voice** reacting.

## Example 2 – Focus on grammar & structure instead of fillers

**Your utterance:**

> Yesterday I had a call with a client and we discuss about the new concept, but at the end nothing was decided because there was too less information and everyone were a bit confuse.
> 

### Signals from the animals

- **GrammarGiraffe**
    - `grammar_verb_tense`: *“we discuss”* → should be *“we discussed”*
    - `grammar_preposition`: *“discuss about”* → should be *“discuss”*
    - `grammar_quantifier`: *“too less information”* → should be *“too little information”*
    - `grammar_agreement`: *“everyone were”* → should be *“everyone was”*
    - `grammar_adjective`: *“a bit confuse”* → should be *“a bit confused”*
    - Severity: **0.9** (many small issues in one sentence)
- **FillerFalcon**
    - No fill­ers → no signal.
- **EchoEagle**
    - Maybe notes mild overuse of “because” in recent turns, but low severity here.
- **PatternPanther**
    - Spots pattern: struggling with **past narrative about meetings** (tense + agreement errors when describing past calls).
- **TempoTiger**
    - Slightly slow pace, but nothing critical → low severity signal.
- **LexiLynx**
    - Notes use of known words: *client, concept, decided* → logs as context for vocab usage.

---

### OrchestratorOctopus in action

Assume today’s focus (from FocusFalcon) is **“grammar accuracy in past-tense narratives”**.

1. **Score signals**
    - GrammarGiraffe’s combined grammar signal: high severity + matches focus
    - PatternPanther’s “past narrative pattern” also relevant, but more long-term
    - Others low or off-focus
2. **Pick real-time intervention**
    - Chooses **GrammarGiraffe’s signal** as the real-time candidate.
    - Bundles the 4–5 issues as **one** micro-drill instead of 5 separate corrections.
3. **Task request to TaskTiger**
    
    > “Design a micro-drill:
    > 
    > - show corrected sentence,
    > - ask user to repeat improved version,
    > - then ask for a *new* example of a past client call, with correct tense & agreement.”

---

### What CoachCoyote says to you

CoachCoyote (using TaskTiger’s drill):

> There are a few small grammar issues in that sentence. Here’s a cleaner version:
> 
> 
> 👉 *“Yesterday I had a call with a client and we discussed the new concept, but in the end nothing was decided because there was too little information and everyone was a bit confused.”*
> 
> 1. Say this improved sentence out loud once.
> 2. Then tell me about another past client call, using the **past tense** and **“everyone was”** correctly.

You get:

- One **compact correction**,
- One **repetition** of the improved sentence,
- One **new production task** to stabilise the pattern.

---

### What happens with the other signals

- **PatternPanther’s “past narrative” pattern**
    - Stored in the **session buffer** → used at end-of-session:
        
        > “Today, most of your grammar issues appeared when you talked about past meetings.”
        > 
    - FocusFalcon may turn this into next week’s mini-theme: *“Past meetings & project updates.”*
- **EchoEagle (mild ‘because’ overuse)**
    - Low severity now → stored for long-term trends.
    - If it becomes frequent, later TaskTiger might design a drill with alternatives:
        
        > “since, as, due to the fact that.”
        > 
- **TempoTiger**
    - Slightly slow pace but nothing urgent → aggregated with other sentences to see if your WPM is consistently low or just fine.

## Mental model summary

- **Listeners (Giraffe, Falcon, Eagle, Panther, Tiger, Lynx)**
    - Watch everything → send signals.
- **OrchestratorOctopus**
    - Collects signals
    - Decides what to act on now vs later
    - Sends requests to TaskTiger or marks them for summaries
- **TaskTiger**
    - Designs the actual drills / exercises.
- **CoachCoyote**
    - Talks to you.
    - Every correction, exercise, or explanation comes from this voice.
- If you *don’t* follow:
    - ScribeSparrow logs it,
    - FocusFalcon & SessionShepherd change how and when issues are addressed,
    - The whole zoo becomes **less interrupting, more strategic**.

### Core MVP animals

**Listeners:**

- 🦒 GrammarGiraffe – catch obvious grammar issues
- 🦅 FillerFalcon – count fillers
- 🐯 TempoTiger – measure basic speed & pauses (optional, but nice)

**Memory:**

- 🐦 NotionNightingale – read from your Notion vocab DB (even read-only at first)
- 🐿️ SpacedSquirrel – *very simple* “due today” list (even without full SM-2 logic at the start)

**Coaches:**

- 🐺 CoachCoyote – the only voice
- 🐯 TaskTiger – 3–4 simple drill types:
    - “Repeat without filler”
    - “Rephrase with a better word”
    - “Try the corrected version once”
- 🐕‍🦺 SessionShepherd – only two modes:
    - quick session (5–7 min)
    - full session (15–20 min)

**Control:**

- 🐙 OrchestratorOctopus – *super simple* rules:
    - At most **1 micro-nudge every 3 user turns**
    - Prioritise *either* fillers *or* grammar, not both

That’s it. No actors, no complicated weekly themes, no deep pattern trends yet.

[🧬 Zoo v1.0 – Final Agent Set](🧬%20Zoo%20v1%200%20–%20Final%20Agent%20Set.md)

[Example Notion](Example%20Notion.md)

[Example 2](Example%202.md)