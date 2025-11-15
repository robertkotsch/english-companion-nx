# 🎻 Flow plan

## 0. Day starts – setting the stage

**Trigger:** Jetson + Companion start inside your 9–5 window.

1. **DayDolphin**
    - Enters `DAY_BOOT`.
    - Asks:
        - “What happened yesterday?” → **ScribeSparrow**
        - “What’s due for review today?” → **SpacedSquirrel**
        - “What’s Rob’s current goals & mode?” → **PersonaPanda**
2. **SessionShepherd + FocusFalcon**
    - Build a **rough plan for today**:
        - X review items from SpacedSquirrel
        - maybe 1 focus (e.g. fillers / grammar / vocab)
    - Store as `today_plan`.
3. **DayDolphin**
    - Switches to `WAITING_FOR_USER`.

🧠 **No coaching yet. Stage is set, animals are waiting.**

---

## 1. You start talking – choosing session mode

**Trigger:** First message / voice input between 9–5.

1. **DayDolphin**
    - Sees “first contact today” → moves to a small decision step:
        - *“Quick session, full session, or just chat?”*
2. **BoundaryBison**
    - Applies **mode & intensity**:
        - coach_mode = `off / soft / normal / intense`.
3. **SessionShepherd**
    - If quick → selects **small subset** of `today_plan`.
    - If full → uses the full workout.
    - If just chat → no formal blocks, but plan stays in the background.
4. **DayDolphin**
    - State becomes:
        - `IN_SESSION` (quick/full) **or**
        - `FREE_CONVERSATION`.

From this moment on, **every utterance** goes through the same inner loop.

---

## 2. Inner loop for each utterance – who listens and who talks

### Step 2.1 – You speak → text appears

- Voice → **STT** (Whisper) → text.
- The utterance + timestamps go to all listeners.

### Step 2.2 – Listeners observe

These **do not talk**; they only emit signals:

- **GrammarGiraffe** – grammar issues
- **FillerFalcon** – fillers
- **EchoEagle** – overused words / vague adjectives
- **PatternPanther** – recurring structures / typical mistakes
- **TempoTiger** – speed, pauses
- **LexiLynx** – which vocab items from Notion are used or could be upgraded
- **PronunciationPenguin** – misheard words / stress issues
- **EmpathyElephant** – skipped drills, short answers, self-critical language

Each sends a **signal** like:

> source, type, severity, scope (utterance/session), realtime_desirable, data…
> 

All signals go to **OrchestratorOctopus** 🐙.

### Step 2.3 – OrchestratorOctopus decides “What now?”

OrchestratorOctopus:

1. Collects all signals for this utterance.
2. Checks:
    - current **session state** (DayDolphin)
    - `coach_mode` & intensity (BoundaryBison)
    - today’s focus (FocusFalcon)
3. Scores signals and does:
- **Real-time queue:**
    - At most **one** thing to act on now (e.g. filler drill, grammar fix, vocab upgrade).
- **Session buffer:**
    - Stores other issues for end-of-session feedback.
- **Trend store:**
    - Aggregates patterns for long-term stats (weekly/monthly).
1. If something should be handled *now*, it sends a **drill request** to **TaskTiger**.

### Step 2.4 – TaskTiger + CoachCoyote act

- **TaskTiger** designs the **concrete exercise**:
    - “Repeat without fillers”
    - “Say the improved sentence”
    - “Use this Notion collocation in a new example”
    - “Give a more precise adjective”
    - “Shadow this line once”
- **CoachCoyote** is the **only voice**:
    - Delivers the feedback/drill in natural language.
    - Keeps tone adapted (EmpathyElephant + PersonaPanda).

If no real-time drill is allowed (soft mode, or too many recent nudges), CoachCoyote may just respond normally and let ScribeSparrow log the issues.

### Step 2.5 – Memory updates

In parallel:

- **NotionNightingale + LexiLynx**
    - Update `vocab_usage` for any target words/collocations used.
    - Add new good expressions back to Notion when needed.
- **SpacedSquirrel**
    - Adjusts intervals for items you practiced.
- **ScribeSparrow**
    - Logs:
        - utterance,
        - drills offered,
        - drills completed/ignored.
- **StoryStork**
    - Tags topic (e-learning, 3D, leadership, fitness…).

Then we loop back and wait for your next utterance.

---

## 3. End of session – wrapping up

**Trigger:** You go idle for a while / say you’re done / state timeout.

1. **DayDolphin**
    - Moves from `IN_SESSION` to `FREE_CONVERSATION` or directly to a short **wrap-up** state.
2. **ScribeSparrow**
    - Builds a **short summary** from the session buffer:
        - main focus areas touched,
        - drills done,
        - one or two key improvements or problem patterns.
3. **CoachCoyote**
    - Presents summary in human terms:
        - “Today your fillers dropped a bit.”
        - “We worked on replacing ‘very good’ with stronger adjectives like ‘excellent’.”
4. **SpacedSquirrel**
    - Finalises SRS scheduling based on today’s success/failure.
5. **FocusFalcon + PersonaPanda**
    - Use ScribeSparrow’s stats to propose **next session focus** (e.g. “next time: more phrasal verbs”).

---

## 4. End of day – long-term brain

**Trigger:** Day ends (after 17:00) or device shuts down.

1. **DayDolphin**
    - Moves to `DAY_OVER`.
2. **ScribeSparrow**
    - Stores daily aggregates:
        - filler rate,
        - major error types,
        - new vocab mastered,
        - listening/shadowing tasks completed.
3. **EmpathyElephant + PersonaPanda**
    - Adjust expectations:
        - too many skipped drills → lighten future plans,
        - strong consistency → maybe raise intensity slightly.
4. Next morning: back to **0. Day starts – setting the stage**.

## One-sentence mental picture

> You talk → listeners watch everything → OrchestratorOctopus decides what matters → TaskTiger turns it into a drill → CoachCoyote talks to you → memory agents update vocab & progress → DayDolphin and friends keep the rhythm of the day.
>