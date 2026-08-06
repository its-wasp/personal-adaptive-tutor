## 2.4 Key Algorithms and Logic

Six algorithms carry the system's adaptive behaviour. Each is given below as
pseudocode with the reasoning behind its parameters; the corresponding source
file is named for each.

### 2.4.1 Mastery estimation

**Source:** `services/knowledge_graph_service.py` → `update_mastery_after_quiz`

The problem: convert a stream of correct/incorrect answers into a single
mastery score in [0, 1] that responds to genuine improvement without
overreacting to one bad answer.

```
ALGORITHM UpdateMastery(user, concept, is_correct)

  m ← mastery row for (user, concept), created at zero if absent

  m.total_interactions ← m.total_interactions + 1
  m.total_answers      ← m.total_answers + 1
  IF is_correct THEN
      m.correct_answers ← m.correct_answers + 1

  accuracy ← m.correct_answers / m.total_answers

  // Blend observed accuracy with the previous estimate rather than
  // replacing it. Pure accuracy is too jumpy early on: a single wrong
  // first answer would read as total mastery 0.
  m.mastery_level ← min(1.0, 0.7 × accuracy + 0.3 × m.mastery_level)

  // Confidence is about evidence volume, not correctness. Ten interactions
  // is treated as enough to trust the estimate.
  m.confidence ← min(1.0, m.total_interactions / 10)

  m.last_reviewed_at ← now()
  RETURN m
```

**On the 70/30 split.** With a weight of 1.0 on accuracy the score oscillates
violently across the first few answers. With too little weight it lags real
improvement by many attempts. At 0.7 a learner who starts answering correctly
after a poor run crosses the 0.6 unlock threshold within three or four correct
answers, which matches the intuition that a few consecutive successes should
count as progress.

**Property.** The score is bounded in [0, 1] and monotone in accuracy for fixed
prior mastery.

### 2.4.2 SM-2 spaced repetition

**Source:** `services/spaced_repetition_service.py` → `update_after_review`

Review intervals should expand for material the learner retains and collapse
for material they do not. SM-2 [2] is the standard treatment.

```
ALGORITHM ScheduleReview(m, is_correct)

  // Map a binary quiz outcome onto SM-2's 0-5 recall quality. A correct
  // answer on already-strong material is easy recall; correct on weak
  // material is recall with effort.
  IF is_correct THEN
      quality ← 5 IF m.mastery_level ≥ 0.7 ELSE 4
  ELSE
      quality ← 1

  // SM-2 ease-factor update. Below quality 3 the factor decreases.
  EF ← m.ease_factor + (0.1 − (5 − quality) × (0.08 + (5 − quality) × 0.02))
  m.ease_factor ← max(1.3, EF)          // 1.3 is SM-2's floor

  IF quality < 3 THEN
      m.review_interval_days ← 1        // reset, not decrement
  ELSE IF m.review_interval_days < 1 THEN
      m.review_interval_days ← 1
  ELSE IF m.review_interval_days = 1 THEN
      m.review_interval_days ← 6
  ELSE
      m.review_interval_days ← round(m.review_interval_days × m.ease_factor, 1)

  m.last_reviewed_at ← now()
  m.next_review_at   ← now() + m.review_interval_days days
```

**On the 1.3 floor.** Without it, repeated failures drive the ease factor toward
zero and the interval collapses permanently, so a concept the learner has since
learned keeps reappearing. The floor guarantees that intervals can always
recover.

**On resetting rather than decrementing.** A missed concept returns tomorrow
regardless of how long the interval had grown. Halving a ninety-day interval
would still leave forty-five days before the learner saw material they had just
demonstrably forgotten.

**Worked example.** Starting at interval 1 day, EF 2.5, three consecutive
correct answers at mastery below 0.7 (quality 4):

| Review | Quality | EF after | Interval | Next due |
|---|---|---|---|---|
| 1 | 4 | 2.50 | 6 days | +6 days |
| 2 | 4 | 2.50 | 15.0 days | +15 days |
| 3 | 4 | 2.50 | 37.5 days | +38 days |
| 4 | 1 (wrong) | 2.14 | 1 day | tomorrow |

Quality 4 leaves the ease factor unchanged — the term evaluates to zero — so
growth is purely geometric until a failure resets it.

### 2.4.3 Prerequisite unlocking

**Source:** `repositories/knowledge_graph_repo.py` → `get_unlocked_concepts`

```
ALGORITHM UnlockedConcepts(user, subject)

  nodes      ← all concept nodes for subject                    // 1 query
  mastery    ← {concept_id → level} for user                    // 1 query
  prereqs    ← {to_id → [from_id]} for PREREQUISITE edges        // 1 query

  unlocked ← []
  FOR each node IN nodes:
      required ← prereqs[node.id] or []
      // all(∅) is true, so root concepts are unlocked by definition
      IF ∀ p ∈ required : mastery[p] ≥ UNLOCK_THRESHOLD THEN
          append node to unlocked

  RETURN unlocked
```

Three queries regardless of graph size. The earlier implementation called a
per-node helper that issued two queries each — roughly fifty extra round trips
across the twenty-five-node graph, on the path the dashboard loads on every
visit.

`UNLOCK_THRESHOLD` is 0.6: high enough to mean genuine competence, low enough
that the graph does not feel locked shut. The frontend mirrors the same rule
client-side to grey out locked cards without a second request.

### 2.4.4 Next-concept recommendation

**Source:** `services/knowledge_graph_service.py` → `get_next_recommended`

```
ALGORITHM RecommendNext(user, subject)

  candidates ← UnlockedConcepts(user, subject)
               filtered to mastery < 0.8            // 0.8 counts as mastered

  IF candidates is empty THEN RETURN none

  // Weakest first; ties broken toward the easier tier so the learner
  // is never handed an expert-tier concept when a foundational one is
  // equally weak.
  sort candidates by (mastery ascending, difficulty_tier ascending)

  RETURN candidates[0]
```

### 2.4.5 Personalized prompt assembly

**Source:** `llm/prompt_builder.py`

The mechanism behind objective O2. The profile is not passed to the model as
data; it is translated into imperative instructions.

```
ALGORITHM BuildSystemPrompt(profile, retrieved_chunks)

  parts ← [ tutor persona ]

  // Block 1 — cross-session memory
  IF profile.learner_summary THEN
      parts += "What you know about this learner from previous sessions:"
      parts += profile.learner_summary
      parts += "Use this to tailor your explanation, but do not mention it."

  // Block 2 — preferences, as instructions rather than facts
  SWITCH profile.learning_style:
      EXAMPLE_FIRST → "Start with a concrete example, THEN the theory."
      THEORY_FIRST  → "Start with the concept, THEN show examples."
      VISUAL        → "Use ASCII diagrams and step-by-step traces."
      READING       → "Use clear, well-structured written prose."

  SWITCH profile.pace_preference:
      QUICK    → "Be concise. Skip obvious detail."
      DETAILED → "Be thorough. Explain every step."

  IF profile.use_analogies THEN
      parts += "Include real-world analogies."

  IF profile.strengths THEN
      parts += "Learner is strong in {strengths} — you may build on these."
  IF profile.weaknesses THEN
      parts += "Learner struggles with {weaknesses} — be extra clear here."

  // Block 3 — retrieved grounding
  IF retrieved_chunks THEN
      parts += "Ground your explanation in the following material."
      FOR each chunk (truncated to 500 characters):
          parts += chunk

  RETURN join(parts)
```

**On truncation.** Chunks are capped at 500 characters and the retrieval limit
at two or three. The budget is real: system prompt, memory, preferences,
references and up to twenty turns of history all compete inside one context
window, and history is what keeps the conversation coherent.

**On hiding the memory.** The model is explicitly told not to mention the
summary. Without that instruction it opens replies by reciting what it
remembers, which is both unnatural and faintly unsettling.

### 2.4.6 Structured output recovery

**Source:** `llm/response_parser.py`, `llm/structured.py`

Language models asked for JSON return *almost* JSON: fenced in markdown,
prefaced with commentary, or containing literal newlines inside string values.
Recovery runs at two levels.

**Level 1 — extraction, four strategies in order:**

```
ALGORITHM ExtractJSON(raw)

  1. Parse raw directly.                            → return on success
  2. Extract from a ```json … ``` fence and parse.  → return on success
  3. Match the outermost { … } and parse.           → return on success
  4. Field-by-field recovery for unescaped newlines:
       locate every "key": in the block
       for each key, take the span up to the next key as its value
                                                    → return on success
  RAISE ValueError
```

Strategy 4 exists because it is the single most common real failure: a model
writing a multi-line code example inside an `"explanation"` string emits raw
newlines, which is invalid JSON but perfectly recoverable.

Extraction is followed by contract validation — an explanation must carry a
non-empty `title` and `explanation`; a quiz must carry a question, at least two
options and a correct option. Silently accepting a blank field once produced
sessions whose opening message was empty, after which the model hallucinated
context on the first real turn.

**Level 2 — the retry ladder:**

```
ALGORITHM GenerateStructured(llm, messages, parse, correction, on_failure)

  TRY
      raw ← llm.generate(messages, temperature=t, json_mode=true)
      RETURN parse(raw)
  CATCH ValueError AS first_error
      // Either our parser failed, or the provider's own JSON validator
      // rejected the generation. Both are recoverable the same way.

  retry ← messages
  IF raw exists THEN retry += assistant turn containing raw
      // A provider-side rejection returns no text, so there is nothing
      // to show the model in that case.
  retry += user turn containing correction

  TRY
      raw₂ ← llm.generate(retry, temperature=t′ < t, json_mode=true)
      RETURN parse(raw₂)
  CATCH ValueError
      RAISE ValueError(on_failure) FROM first_error
```

The retry runs cooler than the first attempt — 0.2 against 0.7 for
explanations, 0.3 against 0.8 for quizzes. The first call wants variety; the
retry only wants compliance.

Exactly one retry. A second has a poor success rate and doubles worst-case
latency on a path the learner is already waiting on. Persistent failure surfaces
as HTTP 502, distinguishing "the upstream model misbehaved" from "our code
broke".

### 2.4.7 Study streak derivation

**Source:** `services/learner_profile_service.py` → `compute_streak`

```
ALGORITHM ComputeStreak(active_dates, today)

  days ← distinct dates, sorted descending
  IF days is empty THEN RETURN 0

  // Yesterday still counts as current: a streak should not die at midnight
  // before the learner has had a chance to study today.
  IF (today − days[0]) > 1 day THEN RETURN 0

  streak ← 1
  FOR each consecutive pair (newer, older) IN days:
      IF (newer − older) ≠ 1 day THEN BREAK
      streak ← streak + 1

  RETURN streak
```

Derived from `engagement_events` rather than separately maintained, so it
cannot drift out of step with actual activity.

{{PAGEBREAK}}
