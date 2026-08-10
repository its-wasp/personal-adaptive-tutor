# CHAPTER 2: IMPLEMENTATION DETAILS

## 2.1 System Architecture and Design

### 2.1.1 Architectural style

The system is a three-tier web application. The backend is split into four
layers, and each layer only calls the one below it.

| Layer | Directory | Responsibility |
|---|---|---|
| Router | `app/routers/` | Parse the request, authenticate, map errors to status codes, serialise the response |
| Service | `app/services/` | Business rules, authorization, algorithms |
| Repository | `app/repositories/` | Database queries |
| Model | `app/models/` | Table definitions |

Two things came out of this that were useful in practice. The access control fix
described in Chapter 3 was a single change in the service layer, and every route
that calls those services picked it up. And because services raise their own
exceptions instead of FastAPI's `HTTPException`, they can be tested without
starting a web server. All 37 tests added during the hardening phase run that
way.

There are two pluggable interfaces. `app/llm/base_provider.py` defines
`generate()`, implemented by `GroqProvider` and selected by a factory from
configuration. `app/search/base_provider.py` does the same for web search. No
service imports Groq directly.

This paid off in one specific case. When Groq's server-side JSON validator
rejects a response it raises a Groq-specific error. `GroqProvider` converts it
into a plain `ValueError`, so the retry logic handles provider rejections and
parse failures through the same path without knowing which provider is in use.

### 2.1.2 High-level architecture

![](../screenshots/fig-2.1-architecture.png)

> **Figure 2.1 — System Architecture.** Source: `docs/diagrams/architecture.mmd`

The diagram separates the personalization components from the rest of the
service layer. Four of them work together on every response:

- **Prompt Builder** assembles the system prompt from the tutor persona, learner
  memory, profile-derived instructions and retrieved reference text.
- **RAG Retriever** embeds the learner's question and finds the closest stored
  explanations.
- **Response Parser** recovers structured output from imperfect model responses.
- **Personalization Reasons** records which signals were used, for display.

### 2.1.3 Data flow

![](../screenshots/fig-2.2a-dfd-level-0.png)

> **Figure 2.2a — Data Flow Diagram, Level 0.** Source: `docs/diagrams/dfd-level-0.mmd`

![](../screenshots/fig-2.2b-dfd-level-1.png)

> **Figure 2.2b — Data Flow Diagram, Level 1.** Source: `docs/diagrams/dfd-level-1.mmd`

The level-1 diagram splits the system into six processes over eight data stores.
Two of them matter most.

Process 3.0, running a tutoring session, reads from three stores before it calls
the model: the profile and learner memory, strengths and weaknesses derived from
mastery, and retrieved reference chunks. Those three coming together is what
makes an explanation personalized rather than generic.

Process 6.0 closes the loop. Conversation history goes back to the model for
summarisation and returns as an updated learner memory, which feeds process 3.0
next time. What the system knows about a learner therefore depends on all their
earlier sessions, not just the current one.

### 2.1.4 Component interaction

![](../screenshots/fig-2.3-component-interaction.png)

> **Figure 2.3 — Component Interaction.** Source: `docs/diagrams/component-interaction.mmd`

Most routes are one router to one service to one repository. Two are wider.
`ChatService` also uses `LearnerProfileService` and `EngagementService`, because
producing one reply needs profile data, retrieval and event tracking together.
`QuizService` is the widest: submitting one answer updates topic progress,
concept mastery, the revision schedule and the engagement log. Keeping that in
one service means the ordering constraint stays in one place, since mastery has
to be updated before the SM-2 code reads it.

### 2.1.5 Database design

![](../screenshots/fig-2.4-er-model.png)

> **Figure 2.4 — Entity-Relationship Model.** Source: `docs/diagrams/er-model.mmd`

Thirteen tables. All inherit a base class giving every row a UUID primary key
and created/updated timestamps. We used UUIDs rather than auto-incrementing
integers because many endpoints take an ID from the client, and sequential IDs
are easy to guess.

A few design points worth explaining:

**Mastery is stored as current state, not a log.** `concept_mastery` has a
unique constraint on `(user_id, concept_node_id)`, so each learner has one row
per concept, updated in place. The full history is still in `quiz_attempts` if
it is ever needed, but the common query, "what does this learner know", is a
single lookup.

**Prerequisites are typed edges.** `concept_edges` has a relation type of
PREREQUISITE, RELATED or EXTENDS. Only PREREQUISITE controls unlocking. One edge
table serves both directions of the graph.

**JSONB only where the shape varies.** `metadata_json` on `chat_messages` holds
a quiz reference for quiz messages and a personalization snapshot for assistant
messages. Storing these as columns would mean a mostly-empty wide table.

**Engagement events survive session deletion.** Deleting a chat session removes
its messages, quizzes and attempts, but only nulls the session reference on
`engagement_events`. Someone who deletes a session should not lose their study
streak as a side effect.

**Vectors live in the same database.** The embedding column is a `vector(384)`
in PostgreSQL rather than a separate vector database. At a few hundred rows a
dedicated store would add another service to run and keep in sync for no real
benefit.

### 2.1.6 Runtime sequences

![](../screenshots/fig-2.5-sequence-chat.png)

> **Figure 2.5 — Sequence, a personalized chat turn.** Source: `docs/diagrams/sequence-chat.mmd`

![](../screenshots/fig-2.6-sequence-quiz-mastery.png)

> **Figure 2.6 — Sequence, quiz submission through mastery and SM-2.** Source: `docs/diagrams/sequence-quiz-mastery.mmd`

Figure 2.5 shows the three personalization sources coming together before the
model call. Figure 2.6 shows why mastery has to be updated before the SM-2 step:
the recall quality mapping reads the new mastery value to choose between quality
4 and quality 5.

## 2.2 Technology Stack

### 2.2.1 Languages

Python 3.11 for the backend, chosen for its LLM and embedding libraries.
JavaScript (ES2022) with plain JSX for the frontend, no TypeScript. SQL for
migrations and the vector similarity queries.

### 2.2.2 Backend

| Library | Role | Why |
|---|---|---|
| FastAPI | Web framework | Dependency injection gives clean per-request DB sessions and a reusable auth dependency; generates API docs from the DTOs |
| Pydantic v2 | Validation | Invalid requests rejected at the boundary; response models make the API contract explicit |
| SQLAlchemy 2.0 | ORM | Declarative models, confined to the repository layer |
| Alembic | Migrations | Versioned schema changes, three so far |
| pgvector | Vector search | Keeps embeddings next to the relational data |
| sentence-transformers | Embeddings | `all-MiniLM-L6-v2` runs locally, no per-embedding API cost |
| groq | LLM client | Fast on the free tier, supports JSON mode |
| python-jose, bcrypt | Auth | JWT signing and password hashing |

### 2.2.3 Frontend

| Library | Role | Why |
|---|---|---|
| React 19 | UI | Suits a stateful chat interface; hooks covered all our state needs |
| Vite 5 | Build | Fast dev server, handles build-time config |
| React Router 7 | Routing | 9 routes; URL-driven state means a refresh keeps your place |
| Tailwind CSS 3 | Styling | Utility classes, responsive breakpoints for the mobile sidebar |
| react-markdown | Rendering | Renders tutor output with raw HTML disabled, which matters for model-generated text |
| rehype-highlight | Code | Syntax highlighting in code blocks |

We deliberately did not use a state management library or a data fetching
library. Context plus local state was enough at this size, and the two hooks in
`useApi.js` cover our cases in 76 lines.

### 2.2.4 Tools and platforms

Docker Compose runs the database, backend and search with one command.
PostgreSQL 15 using the pgvector image. Git and GitHub for version control
across three contributors, with GitHub Actions for CI. Testing uses pytest and
Vitest with React Testing Library. Quality and security checks use ruff, ESLint,
CodeQL, pip-audit and Trivy. Deployment targets Render for the backend and
Vercel for the frontend.

## 2.3 System Modules

**Authentication** (`auth_router`, `auth_service`, `utils/security.py`). Signup
hashes the password with bcrypt and issues a 24-hour JWT. `get_current_user` is
a FastAPI dependency that decodes the token and loads the user, so no protected
route can accidentally skip authentication. Login returns the same message
whether the email is unknown or the password is wrong, so it cannot be used to
find out which accounts exist.

**Learner profile** (`learner_profile_service`, `prompt_builder`,
`personalization_reasons`). Holds the stated preferences and the derived state.
`get_personalization_context` builds the dictionary the prompt builder consumes:
preferences, strengths (mastery at or above 0.7), weaknesses (below 0.4 with at
least one answer recorded), and the accumulated memory. Every five messages the
service asks the model to update that memory, telling it to merge rather than
replace and to trust newer evidence where the two conflict. If that call fails
it is logged and ignored, since a summarisation error should not cost the
learner their reply.

**Knowledge graph** (`knowledge_graph_service`, `knowledge_graph_repo`,
`dsa_graph.json`). 25 concepts in 5 tiers with 37 typed edges, seeded from JSON.
Provides the graph with mastery overlaid, the unlocked set, and the
next-concept recommendation. Mastery updates blend 70% observed accuracy with
30% previous mastery so one wrong answer does not wipe out a good record.

**Chat** (`chat_service`). Owns sessions and messages. Session creation calls
the model before saving anything, so a generation failure does not leave an
empty session behind. Past 20 messages the service switches to a generated
summary plus the last 10 turns, which keeps token usage roughly flat as a
session grows.

**Quiz** (`quiz_service`). Generates one question at a time, aimed at recorded
weak areas where there are any. Grading is server-side, and the answer, hint and
explanation are withheld until an attempt exists. Submitting an answer updates
topic progress, concept mastery, the SM-2 schedule and the engagement log.

**Spaced repetition** (`spaced_repetition_service`). SM-2 over quiz results,
described in section 2.4.

**RAG** (`rag/`). The seeder writes beginner, intermediate and advanced
explanations for each concept and embeds them. At query time the retriever
embeds the question and returns the nearest chunks. If sentence-transformers is
not installed the embedder reports itself unavailable, the retriever returns
nothing, and the prompt builder leaves out the reference block. This is what
makes the smaller cloud image possible.

**Onboarding** (`onboarding_service`). Ten fixed placement questions across
tiers 1 to 4. They are fixed rather than generated so placement is consistent
between learners and costs no LLM call. Per-concept accuracy seeds initial
mastery, capped at 0.6 because a placement quiz is weak evidence.

### 2.3.1 Functional flow

1. Sign up, account created and token issued
2. Onboarding step 1, preferences saved
3. Onboarding step 2, placement quiz seeds mastery
4. Dashboard shows concepts by tier with mastery, locks and a recommendation
5. Start a session, opening explanation generated from the profile
6. Converse, memory updated every five messages
7. Take a quiz, mastery updates
8. Mastery passes 0.6 and dependent concepts unlock
9. SM-2 schedules the concept for review
10. Return later and the tutor still has the accumulated memory

{{PAGEBREAK}}
