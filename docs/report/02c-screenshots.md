## 2.5 Screenshots and Key Code Sections

### 2.5.1 Application screenshots

Capture instructions and filenames are in
`docs/screenshots/SCREENSHOT-CHECKLIST.md`.

> **Figure 2.7 — Onboarding, preference selection.** The four settings that
> shape every subsequent explanation.

> **Figure 2.8 — Onboarding, placement quiz.** Ten questions spanning tiers
> one to four, seeding initial mastery across the graph.

> **Figure 2.9 — Dashboard.** Twenty-five concepts in five tiers, with mastery
> bars, prerequisite chips, padlocks on locked concepts, the recommendation
> card and the progress summary.

> **Figure 2.10 — Concept detail panel.** Mastery, prerequisites, estimated
> time and the level selector for starting a session.

> **Figure 2.11 — Tutoring session.** A personalized explanation with
> markdown formatting and syntax-highlighted code.

> **Figure 2.12 — "Why this response", expanded.** The personalization
> signals that shaped the message above it.

> **Figure 2.13 — Inline quiz, after submission.** The correct option
> highlighted, the learner's incorrect choice marked, explanation and hint
> revealed.

> **Figure 2.14 — Review queue.** Concepts due under the SM-2 schedule, with
> mastery, interval and days overdue.

> **Figure 2.15 — Profile.** Editable preferences alongside the accumulated
> tutor memory.

> **Figure 2.16 — Personalization comparison.** The same concept explained to
> an example-first learner and a theory-first learner, side by side. This is
> the figure that demonstrates the central claim rather than asserting it.

### 2.5.2 Key code sections

**Listing 2.1 — Translating a learner profile into prompt instructions.**
`app/llm/prompt_builder.py`. The core of objective O2: preferences become
imperatives, not data.

```python
def build_personalization_block(profile: dict) -> str:
    lines = ["Adapt your response to this learner's profile:"]

    style = profile.get("learning_style", "not set")
    if style == "EXAMPLE_FIRST":
        lines.append("- Start with a concrete example, THEN explain the theory behind it.")
    elif style == "THEORY_FIRST":
        lines.append("- Start with the concept/theory, THEN show examples.")
    elif style == "VISUAL":
        lines.append("- Use diagrams (ASCII art), visual analogies, and step-by-step traces.")
    elif style == "READING":
        lines.append("- Use clear written explanations with well-structured paragraphs.")

    strengths = profile.get("strengths", [])
    if strengths:
        lines.append(f"- The learner is strong in: {', '.join(strengths)}. "
                     f"You can reference these.")

    weaknesses = profile.get("weaknesses", [])
    if weaknesses:
        lines.append(f"- The learner struggles with: {', '.join(weaknesses)}. "
                     f"Be extra clear here.")

    return "\n".join(lines)
```

**Listing 2.2 — Evolving the learner memory.**
`app/services/learner_profile_service.py`. The prompt instructs the model to
merge rather than replace, and to prefer newer evidence on conflict — which is
what makes the summary accumulate understanding instead of resetting each time.

```python
prompt = f"""You are analyzing a learning session to build a learner profile summary.

EXISTING LEARNER SUMMARY:
{existing_summary}

RECENT CONVERSATION (topic: {topic}):
{conversation_text}

Based on the conversation above, update the learner summary. The summary should capture:
- How this learner thinks and approaches problems
- What explanations or styles helped them understand (or didn't)
- Specific concepts they grasped quickly or struggled with
- Patterns in their questions (do they ask for examples? formal definitions? analogies?)

Keep it concise (3-5 sentences). Write in third person ("This learner...").
Merge new observations with the existing summary — don't repeat, evolve it.
If the existing summary contradicts what you see now, trust the newer evidence.

Return ONLY the updated summary text, nothing else."""
```

**Listing 2.3 — The session ownership guard.**
`app/services/chat_service.py`. One method, called by every entry point that
accepts a caller-supplied session identifier. The comment records *why* it
conflates the two failure cases.

```python
def _assert_owns_session(self, chat_session_id, user_id) -> ChatSession:
    """
    Return the session only if `user_id` owns it.

    Every entry point that takes a caller-supplied chat_session_id must go
    through here. A session that exists but belongs to someone else raises
    the same error as one that doesn't exist, so the response can't be used
    to probe for valid session ids.
    """
    session = self.repo.get_session(chat_session_id)
    if not session or str(session.user_id) != str(user_id):
        raise NotFoundError("Chat session not found")
    return session
```

**Listing 2.4 — SM-2 interval scheduling.**
`app/services/spaced_repetition_service.py`. Binary quiz outcomes are mapped
onto SM-2's recall-quality scale, then the standard ease-factor arithmetic
applies.

```python
if is_correct:
    quality = 5 if mastery.mastery_level >= 0.7 else 4
else:
    quality = 1

ef = mastery.ease_factor
ef = ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
mastery.ease_factor = max(1.3, ef)          # SM-2 minimum is 1.3

if quality < 3:
    mastery.review_interval_days = 1.0      # failed — see it again tomorrow
elif mastery.review_interval_days == 1.0:
    mastery.review_interval_days = 6.0
else:
    mastery.review_interval_days = round(
        mastery.review_interval_days * mastery.ease_factor, 1
    )

mastery.next_review_at = datetime.utcnow() + timedelta(
    days=mastery.review_interval_days
)
```

**Listing 2.5 — Vector similarity retrieval.**
`app/repositories/embedding_repo.py`. Cosine distance in the database, with
optional narrowing to a concept.

```python
query = self.db.query(ContentEmbedding).filter(
    ContentEmbedding.embedding.isnot(None)
)

if concept_node_id:
    query = query.filter(ContentEmbedding.concept_node_id == concept_node_id)

# Order by cosine distance (smaller = more similar)
query = query.order_by(
    ContentEmbedding.embedding.cosine_distance(query_vector)
)

return query.limit(limit).all()
```

**Listing 2.6 — Recovering JSON from imperfect model output.**
`app/llm/response_parser.py`. Strategy four handles the most common real
failure: a multi-line code example inside a string value, which produces
invalid JSON that is nonetheless recoverable.

```python
def _extract_json(raw: str) -> dict:
    # Strategy 1: direct parse
    result = _try_parse(raw)
    if result:
        return result

    # Strategy 2: extract from ```json ... ``` fences
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", raw, re.DOTALL)
    if match:
        result = _try_parse(match.group(1))
        if result:
            return result

    # Strategy 3: first { ... } block
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        block = match.group(0)
        result = _try_parse(block)
        if result:
            return result

        # Strategy 4: unescaped newlines inside string values
        result = _extract_json_with_unescaped_newlines(block)
        if result:
            return result

    raise ValueError(f"Could not extract valid JSON from LLM response: {raw[:500]}")
```

**Listing 2.7 — Snapshotting the personalization signals.**
`app/services/chat_service.py`. Persisted with the message rather than
recomputed at render time, so an older message continues to reflect the
profile that actually produced it.

```python
# Snapshot the signals that shaped this message. We persist them
# (rather than recomputing at render time) because the profile
# evolves — older messages should reflect the profile they were
# actually generated with.
reasons = build_reasons(profile, retrieved)
message = ChatMessage(
    chat_session_id=session.id,
    role=MessageRole.ASSISTANT,
    message_type=MessageType.EXPLANATION,
    content=parsed["explanation"],
    metadata_json={"reasons": reasons} if reasons else None,
)
```

**Listing 2.8 — Stale-response protection in the data hook.**
`frontend/src/hooks/useApi.js`. A counter invalidates in-flight responses when
the path changes, so a slow fetch for one chat session cannot render inside
another.

```javascript
const activeRef = useRef(0);

const fetchNow = useCallback(async () => {
  if (skip || !path) return;
  const id = ++activeRef.current;
  setLoading(true);
  setError(null);
  try {
    const result = await api.get(path);
    if (id === activeRef.current) setData(result);
  } catch (err) {
    if (id === activeRef.current) {
      setError(err instanceof ApiError ? err : new ApiError(0, String(err)));
    }
  } finally {
    if (id === activeRef.current) setLoading(false);
  }
}, [path, skip]);
```

{{PAGEBREAK}}
