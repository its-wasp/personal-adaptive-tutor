## 2.5 Screenshots and Key Code Sections

### 2.5.1 Screenshots

![](../screenshots/fig-2.7-onboarding-preferences.png)

> **Figure 2.7 — Onboarding, preference selection.** The four settings that
> shape later explanations.

![](../screenshots/fig-2.8-onboarding-placement.png)

> **Figure 2.8 — Placement quiz.** Ten questions across tiers one to four,
> seeding initial mastery.

![](../screenshots/fig-2.9-dashboard.png)

> **Figure 2.9 — Dashboard.** Concepts in five tiers with mastery bars,
> prerequisite chips, locks, the recommendation card and the progress summary.

![](../screenshots/fig-2.10-concept-detail.png)

> **Figure 2.10 — Concept detail panel.** Mastery, prerequisites and the level
> selector for starting a session.

![](../screenshots/fig-2.11-chat-session.png)

> **Figure 2.11 — Tutoring session.** A personalized explanation with markdown
> and highlighted code.

![](../screenshots/fig-2.12-why-this-response.png)

> **Figure 2.12 — "Why this response", expanded.** The signals that shaped the
> message above it.

![](../screenshots/fig-2.13-quiz-answered.png)

> **Figure 2.13 — Quiz after submission.** Correct option in green, the wrong
> pick in red, explanation and hint shown.

![](../screenshots/fig-2.14-review-queue.png)

> **Figure 2.14 — Review queue.** Concepts due under the SM-2 schedule.

![](../screenshots/fig-2.15-profile.png)

> **Figure 2.15 — Profile.** Editable preferences and the tutor's memory.

![](../screenshots/fig-2.16-personalization-comparison.png)

> **Figure 2.16 — Personalization comparison.** The same concept explained to an
> example-first and a theory-first learner, side by side.

### 2.5.2 Key code sections

**Listing 2.1 — Turning the profile into prompt instructions**
(`app/llm/prompt_builder.py`). This is the core of objective O2.

```python
def build_personalization_block(profile: dict) -> str:
    lines = ["Adapt your response to this learner's profile:"]

    style = profile.get("learning_style", "not set")
    if style == "EXAMPLE_FIRST":
        lines.append("- Start with a concrete example, THEN explain the theory.")
    elif style == "THEORY_FIRST":
        lines.append("- Start with the concept/theory, THEN show examples.")
    elif style == "VISUAL":
        lines.append("- Use diagrams (ASCII art) and step-by-step traces.")

    weaknesses = profile.get("weaknesses", [])
    if weaknesses:
        lines.append(f"- The learner struggles with: {', '.join(weaknesses)}. "
                     f"Be extra clear here.")

    return "\n".join(lines)
```

**Listing 2.2 — Updating the learner memory**
(`app/services/learner_profile_service.py`). The instruction to merge rather
than replace is what makes the summary accumulate instead of resetting.

```python
prompt = f"""You are analyzing a learning session to build a learner profile summary.

EXISTING LEARNER SUMMARY:
{existing_summary}

RECENT CONVERSATION (topic: {topic}):
{conversation_text}

Keep it concise (3-5 sentences). Write in third person ("This learner...").
Merge new observations with the existing summary — don't repeat, evolve it.
If the existing summary contradicts what you see now, trust the newer evidence.

Return ONLY the updated summary text, nothing else."""
```

**Listing 2.3 — The session ownership guard** (`app/services/chat_service.py`).
Called by every entry point that takes a session ID from the client.

```python
def _assert_owns_session(self, chat_session_id, user_id) -> ChatSession:
    """
    Return the session only if `user_id` owns it.

    A session that exists but belongs to someone else raises the same error
    as one that doesn't exist, so the response can't be used to probe for
    valid session ids.
    """
    session = self.repo.get_session(chat_session_id)
    if not session or str(session.user_id) != str(user_id):
        raise NotFoundError("Chat session not found")
    return session
```

**Listing 2.4 — SM-2 scheduling**
(`app/services/spaced_repetition_service.py`).

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
```

**Listing 2.5 — Vector similarity search**
(`app/repositories/embedding_repo.py`).

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

**Listing 2.6 — Stale response protection** (`frontend/src/hooks/useApi.js`). A
counter invalidates responses that arrive after the path has changed, so a slow
fetch for one chat session cannot render inside another.

```javascript
const activeRef = useRef(0);

const fetchNow = useCallback(async () => {
  if (skip || !path) return;
  const id = ++activeRef.current;
  setLoading(true);
  try {
    const result = await api.get(path);
    if (id === activeRef.current) setData(result);
  } catch (err) {
    if (id === activeRef.current) setError(err);
  } finally {
    if (id === activeRef.current) setLoading(false);
  }
}, [path, skip]);
```

{{PAGEBREAK}}
