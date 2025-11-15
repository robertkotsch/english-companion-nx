# Example Notion

## 🗣️ 1. Your utterance

Topic: your work at chemmedia.

> I often have to make the content better and explain things in a more easy way so that the client can understand it.
> 

(We’ll fix language via the coach later.)

---

## 🐾 2. What the animals see

### GrammarGiraffe 🦒

- Notices minor issues:
    - “in a more easy way” → more natural: “in a simpler way” / “more simply”
- Sends a low–medium severity grammar signal.

---

### LexiLynx 🐈‍⬛ (Vocabulary Usage Tracker) + NotionNightingale 🐦 (Notion sync)

LexiLynx:

1. Detects **context**: content development / explanation.
2. Spots basic phrases:
    - “make the content better”
    - “explain things in an easy way”

It asks **NotionNightingale**:

> “Give me entries from Notion in categories related to:
> 
> - Content Development Verbs
> - Explaining / Communication Verbs”

NotionNightingale looks up your Notion table and finds a row like:

- **Verb Category:** Content Development Verbs
- **Main Verb + Collocation:** *refine material* / *polish content*
- **Synonyms (Main Verb):** improve, enhance
- **Relevant Phrasal Verbs:** brush up on, work on
- **Positive Adjectives:** clear, concise
- **Idioms:** *get the message across*

It then returns this to LexiLynx as a **candidate upgrade**.

LexiLynx creates a signal:

```json
{
  "source": "LexiLynx",
  "type": "vocab_from_notion",
  "severity": 0.8,
  "scope": "utterance",
  "realtime_desirable": true,
  "data": {
    "context": "content_development",
    "notion_id": "row_123",
    "suggestions": {
      "make the content better": ["refine the material", "polish the content"],
      "explain things in an easy way": ["explain it more clearly", "make the explanation simpler"]
    }
  }
}

```

---

### EchoEagle 🦅 & others

- EchoEagle: may flag generic “better” / “easy” → vague but not critical.
- PatternPanther: notes this is a **typical context** for you (content work).
- TempoTiger, FillerFalcon: nothing urgent here.

---

## 🐙 3. OrchestratorOctopus decides

Assume today’s focus from **FocusFalcon** is:

> “Use more precise, professional collocations in work contexts.”
> 

So OrchestratorOctopus:

1. Sees:
    - LexiLynx’s `vocab_from_notion` signal (high severity, on-focus)
    - GrammarGiraffe’s minor issue (off-focus, lower severity)
2. Picks **LexiLynx’s Notion-based signal** as the **real-time intervention**.
3. Sends a request to **TaskTiger**:

> “Design a drill that:
> 
> - replaces ‘make the content better’ with ‘refine the material’ or ‘polish the content’,
> - replaces ‘explain things in an easy way’ with a clearer collocation from Notion,
> - asks Rob to reuse one collocation in a fresh sentence about his work.”

GrammarGiraffe’s minor issue is stored in the **session buffer** for later feedback.

---

## 🐯 4. TaskTiger creates the drill → CoachCoyote talks to you

CoachCoyote:

> Your sentence is clear, but we can make it sound more professional using some of your own Notion vocabulary.
> 
> 
> You said:
> 
> 👉 *“I often have to **make the content better** and **explain things in a more easy way** so that the client can understand it.”*
> 

> From your vocabulary list, you already have some great collocations:
> 
> - **refine the material** / **polish the content**
> - **explain it more clearly** / **make the explanation simpler**

> A more natural version could be:
> 
> 
> 👉 *“I often have to **refine the material** and **explain it more clearly** so that the client can understand it.”*
> 

Then, the drill:

1. **Repeat once**
    
    > “First, say this improved version once.”
    > 
2. **New production using the Notion collocation**
    
    > “Now, give me another example from your work where you had to polish the content before a client presentation.”
    > 

Behind the scenes, LexiLynx checks if you actually used “refine the material” or “polish the content”.

---

## 📚 5. What happens in Notion (and locally)

### A. Updating usage & review

- **LexiLynx** updates the local DB:
    - For `notion_id = row_123` (“refine material / polish content”):
        - `times_seen += 1`
        - if you used one correctly → `times_used_correctly += 1`
- **SpacedSquirrel**:
    - Sees that this collocation was actively practised.
    - Schedules it for review (e.g. in 2–3 days).

---

### B. Pushing new expression *into* Notion (if needed)

Imagine in your new sentence you say:

> “Before the workshop, I always polish the content until it’s crystal clear for the client.”
> 

If “crystal clear” is **not yet** in your Notion DB, then:

- LexiLynx flags this as a nice expression (based on frequency and naturalness).
- NotionNightingale creates or updates a row:
    - **Verb Category:** Communication / Clarity
    - **Main Verb + Collocation:** *make something crystal clear*
    - **Positive Adjectives / idioms:** *crystal clear*
    - **Example sentence:** your own workshop sentence.
- Now “crystal clear” becomes part of your **official** vocab set, available for future drills.

So Notion isn’t just a reference – it’s **growing with your real speech**.

---

### C. Later session: Spaced repetition from Notion

A few days later, during a quick session:

- **SpacedSquirrel** sees that “refine the material / polish the content” is **due today**.
- **SessionShepherd** includes it in your warm-up:
    - CoachCoyote:
        
        > “Quick review: Describe a recent project where you had to refine the material before showing it to the client.”
        > 

The origin of that collocation is still your Notion entry, but now it’s reinforced by real use.