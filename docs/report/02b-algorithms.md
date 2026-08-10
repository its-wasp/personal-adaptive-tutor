## 2.4 Key Algorithms and Logic

### 2.4.1 Mastery estimation

Source: `services/knowledge_graph_service.py`

The problem is turning a stream of right and wrong answers into a single score
between 0 and 1 that responds to real improvement without swinging wildly on one
bad answer.

```
ALGORITHM UpdateMastery(user, concept, is_correct)
  m ← mastery row, created at zero if it does not exist
  m.total_answers ← m.total_answers + 1
  IF is_correct THEN m.correct_answers ← m.correct_answers + 1

  accuracy ← m.correct_answers / m.total_answers
  m.mastery_level ← min(1.0, 0.7 × accuracy + 0.3 × m.mastery_level)
  m.confidence    ← min(1.0, m.total_interactions / 10)
```

We blend rather than replace because pure accuracy is too jumpy early on. One
wrong first answer would read as mastery 0. At a weight of 0.7 a learner who
starts answering correctly after a bad run crosses the 0.6 unlock threshold in
three or four correct answers, which felt about right when we tried it.

Confidence is separate and measures how much evidence there is, not how well the
learner did.

### 2.4.2 SM-2 spaced repetition

Source: `services/spaced_repetition_service.py`

Review intervals should grow for material the learner remembers and shrink for
material they do not. We used SM-2 [2].

```
ALGORITHM ScheduleReview(m, is_correct)
  IF is_correct THEN
      quality ← 5 IF m.mastery_level ≥ 0.7 ELSE 4
  ELSE
      quality ← 1

  EF ← m.ease_factor + (0.1 − (5 − quality) × (0.08 + (5 − quality) × 0.02))
  m.ease_factor ← max(1.3, EF)

  IF quality < 3 THEN
      m.review_interval_days ← 1
  ELSE IF m.review_interval_days = 1 THEN
      m.review_interval_days ← 6
  ELSE
      m.review_interval_days ← m.review_interval_days × m.ease_factor

  m.next_review_at ← now() + m.review_interval_days days
```

The 1.3 floor on the ease factor matters. Without it, repeated failures push the
factor towards zero and the interval never recovers, so a concept the learner
has since learned keeps coming back forever.

We reset the interval to one day on failure rather than halving it. Halving a
90-day interval still leaves 45 days before the learner sees something they have
just demonstrably forgotten.

Starting from interval 1 and ease factor 2.5, with correct answers below 0.7
mastery:

| Review | Quality | Ease factor | New interval |
|---|---|---|---|
| 1 | 4 | 2.50 | 6 days |
| 2 | 4 | 2.50 | 15 days |
| 3 | 4 | 2.50 | 37.5 days |
| 4 | 1 (wrong) | 2.14 | 1 day |

Quality 4 leaves the ease factor unchanged, so growth is geometric until a
failure resets it.

### 2.4.3 Prerequisite unlocking

Source: `repositories/knowledge_graph_repo.py`

```
ALGORITHM UnlockedConcepts(user, subject)
  nodes   ← all concept nodes for subject          -- 1 query
  mastery ← {concept_id → level} for user          -- 1 query
  prereqs ← {to_id → [from_id]} for PREREQUISITE   -- 1 query

  RETURN [ node FOR node IN nodes
           IF every prereq of node has mastery ≥ 0.6 ]
```

Three queries whatever the graph size. An earlier version called a helper per
node that issued two queries each, which was about fifty extra round trips on
the 25-node graph, on the path the dashboard loads every time.

The threshold is 0.6: high enough to mean something, low enough that the graph
does not feel locked shut. The frontend applies the same rule client-side to
grey out locked cards without a second request.

### 2.4.4 Personalized prompt assembly

Source: `llm/prompt_builder.py`

This is the mechanism behind objective O2. The profile is not passed to the
model as data; it is turned into instructions.

```
ALGORITHM BuildSystemPrompt(profile, retrieved_chunks)
  parts ← [ tutor persona ]

  IF profile.learner_summary THEN
      parts += "What you know about this learner from previous sessions:"
      parts += profile.learner_summary
      parts += "Use this to tailor your explanation, but do not mention it."

  SWITCH profile.learning_style
      EXAMPLE_FIRST → "Start with a concrete example, THEN the theory."
      THEORY_FIRST  → "Start with the concept, THEN show examples."
      VISUAL        → "Use ASCII diagrams and step-by-step traces."
      READING       → "Use clear, well-structured written prose."

  IF profile.weaknesses THEN
      parts += "Learner struggles with {weaknesses}. Be extra clear here."

  IF retrieved_chunks THEN
      parts += "Ground your explanation in the following material."
      parts += each chunk, truncated to 500 characters
```

Chunks are capped at 500 characters and retrieval at two or three results. The
system prompt, memory, preferences, references and up to twenty turns of history
all share one context window, and the history is what keeps the conversation
coherent.

The instruction not to mention the summary is there because without it the model
opens replies by reciting what it remembers, which reads oddly.

### 2.4.5 Recovering structured output

Source: `llm/response_parser.py`, `llm/structured.py`

Models asked for JSON usually return something close to JSON: wrapped in
markdown fences, prefixed with a sentence, or with literal newlines inside
string values. Recovery happens at two levels.

Extraction tries four strategies in order:

```
1. Parse the response directly
2. Extract from a ```json ... ``` fence and parse
3. Match the outermost { ... } and parse
4. Walk the block key by key, taking each value as the text
   up to the next key
```

Strategy 4 is the one that earns its place. A model writing a multi-line code
example inside an `"explanation"` string produces raw newlines, which is invalid
JSON but perfectly recoverable.

After extraction the result is checked against a contract. An explanation needs
a non-empty title and explanation; a quiz needs a question, at least two options
and a correct option. We added this after empty fields produced sessions whose
opening message was blank, which made the model invent context on the next turn.

If either step fails, the caller retries once at a lower temperature with a
correction message appended, then gives up with an error the router turns into a
502. One retry only: a second has a poor success rate and doubles the wait on a
path the learner is already sitting through.

### 2.4.6 Study streak

Source: `services/learner_profile_service.py`

```
ALGORITHM ComputeStreak(active_dates, today)
  days ← distinct dates, newest first
  IF days is empty THEN RETURN 0
  IF (today − days[0]) > 1 day THEN RETURN 0

  streak ← 1
  FOR each consecutive pair (newer, older) IN days
      IF (newer − older) ≠ 1 day THEN BREAK
      streak ← streak + 1
  RETURN streak
```

Yesterday still counts as current, so a streak does not disappear at midnight
before the learner has had a chance to study that day. It is derived from
engagement events rather than kept as a separate counter, so it cannot drift out
of step with what the learner actually did.

{{PAGEBREAK}}
