# Example

## 🗣️ 1. Your utterance

You say:

> The presentation was very good and the feedback from many people was very positive. It was nice because we could speak about many things and the client was also very happy.
> 

---

## 🐾 2. Signals from the zoo

### GrammarGiraffe 🦒

- Checks grammar:
    - Tenses: OK
    - Articles: OK
    - Agreement: OK
- Result: **no critical grammar errors → low-severity or no signal**.

---

### FillerFalcon 🦅

- No *“uhm, like, you know”* → **no filler signal**.

---

### EchoEagle 🦅 (Overuse Monitor)

- Notices vague / repetitive adjectives & intensifiers:
    - “very good”
    - “very positive”
    - “nice”
    - “many people”
    - “many things”
    - “very happy”
- Creates a signal:

```json
{
  "source": "EchoEagle",
  "type": "lexical_vagueness",
  "severity": 0.8,
  "scope": "utterance",
  "realtime_desirable": true,
  "data": {
    "vague_adjectives": ["good", "positive", "nice", "happy"],
    "intensifier": "very",
    "repetition": { "many": 2 }
  }
}

```

---

### LexiLynx 🐈‍⬛ (Vocab Usage Tracker)

- Recognises topic: **presentation / client feedback**.
- Checks your vocab database (via NotionNightingale) and finds possible “upgrade” words in categories like **Communication Verbs / Evaluation Adjectives**:
    - “insightful”, “engaging”, “constructive”, “enthusiastic”, “thorough”, “valuable”
- Creates a signal:

```json
{
  "source": "LexiLynx",
  "type": "lexical_upgrade_opportunity",
  "severity": 0.7,
  "scope": "utterance",
  "realtime_desirable": true,
  "data": {
    "context": "presentation_feedback",
    "candidate_upgrades": [
      {"from": "very good", "to": ["excellent", "outstanding"]},
      {"from": "very positive", "to": ["highly positive", "enthusiastic"]},
      {"from": "nice", "to": ["engaging", "enjoyable"]},
      {"from": "very happy", "to": ["delighted", "really satisfied"]}
    ]
  }
}

```

---

### PatternPanther panther (Sentence Pattern Profiler)

- Detects pattern:
    - You often describe things with **“good / nice / positive / happy” + “very”**.
- Sends a **session-level** signal (not urgent):

```json
{
  "source": "PatternPanther",
  "type": "repeated_vague_evaluation",
  "severity": 0.6,
  "scope": "session",
  "realtime_desirable": false}

```

---

### TempoTiger 🐯

- WPM and pauses are fine → maybe a small low-severity signal, but nothing important now.

---

## 🐙 3. OrchestratorOctopus decides what to do

Assume today’s main focus from **FocusFalcon** is:

> “Lexical upgrade – stronger, more precise adjectives in work contexts.”
> 

So:

1. OrchestratorOctopus collects all signals.
2. It scores them:
    - EchoEagle’s **lexical_vagueness**: severity 0.8 × (high focus weight) → **high priority**
    - LexiLynx’s **lexical_upgrade_opportunity**: severity 0.7, also on focus → **almost as high**
    - PatternPanther’s session-level pattern: not real-time
    - TempoTiger: low, off-focus
3. It decides:
    - **Real-time queue**: take the combination of EchoEagle + LexiLynx (they fit together nicely).
    - **Session buffer**: store PatternPanther’s pattern for later summary.
4. It creates a drill request for **TaskTiger**:

> “Design a short lexical upgrade drill:
> 
> - show an improved version of one sentence,
> - ask Rob to say that improved sentence,
> - then ask him to describe the same situation again using at least one strong adjective.”

---

## 🐯 4. TaskTiger designs the drill → CoachCoyote talks to you

### Step 1 – CoachCoyote gives feedback

CoachCoyote:

> Your sentence is clear, but you’re using quite a few vague adjectives like “good, nice, positive, happy” and “very” repeatedly.
> 
> 
> Let me show you a stronger version:
> 

> 👉 “The presentation was excellent, and we received enthusiastic feedback from several participants. It was engaging, because we could dive into several important topics, and the client seemed really satisfied.”
> 

### Step 2 – Easy repetition

> First, try saying this improved version once, in your own words.
> 

(You speak; Whisper transcribes; LexiLynx logs which upgraded words you actually used.)

### Step 3 – New production, with constraints

Then CoachCoyote:

> Now, tell me again about that presentation, but this time:
> 
> - don’t use **“very”**
> - avoid **“good, nice, positive, happy”**
> - instead use at least **two stronger adjectives**, like *“excellent, engaging, constructive, enthusiastic, thorough, valuable”*.

Behind the scenes, LexiLynx will check if you actually used one or two of those.

---

## 📊 5. What happens in the background after this drill

### A. Logging and usage updates

- **LexiLynx**:
    - updates `vocab_usage` for any upgraded adjectives you used (e.g. “excellent”, “enthusiastic”).
    - if some were *suggested but not used*, they remain low-confidence items.
- **SpacedSquirrel**:
    - sees new items used correctly → schedules them for future review (e.g. in 2 days).
    - if you struggled, schedules them sooner or flags them as “needs more support”.
- **NotionNightingale**:
    - if an expression isn’t in your Notion table yet (e.g. “enthusiastic feedback” as a collocation), it can:
        - create a new row, or
        - append to an existing row under “Positive adjectives / collocations”.

---

### B. Pattern & progress

- **PatternPanther**:
    - logs that this drill addressed the “vague evaluation” pattern.
    - if over weeks you still heavily rely on “good / nice / very”, it keeps this on the radar for future sessions.
- **ScribeSparrow**:
    - records:
        - drill type: lexical upgrade
        - issue: vague adjectives
        - outcome: completed / partially completed
    - this is used in end-of-day / weekly summaries.

---

### C. Possible end-of-session summary

At the end of the session, CoachCoyote might say (based on ScribeSparrow + PatternPanther):

> Today, we focused a bit on lexical upgrade.
> 
> 
> You moved from *“very good / very positive / nice / happy”* to combinations like *“excellent, enthusiastic, engaging, really satisfied”*.
> 
> Next time you describe client feedback, try to use at least one upgraded adjective again.
>