# CHAPTER 2: IMPLEMENTATION DETAILS

## 2.1 System Architecture and Design

### 2.1.1 Architectural style

The system is a three-tier web application whose backend is internally divided
into four layers. Each layer may call only the one beneath it.

| Layer | Directory | Responsibility | Must not |
|---|---|---|---|
| Router | `app/routers/` | HTTP concerns: parse request, authenticate, map exceptions to status codes, serialise via DTO | Contain business rules or query the database |
| Service | `app/services/` | Business rules: authorization, orchestration, algorithms | Know about HTTP, or issue raw SQL |
| Repository | `app/repositories/` | Data access: queries, persistence | Contain business rules |
| Model | `app/models/` | Schema: tables, columns, relationships | Contain behaviour |

The discipline pays off in two visible places. The whole ownership-check fix
described in Chapter 3 was a service-layer change, applied once and inherited by
every route that calls those services. And because services raise domain
exceptions such as `NotFoundError` rather than `HTTPException`, they are
directly testable without a web framework — every one of the 37 tests added
during hardening runs without starting a server.

Two extension points use the same abstract-base-class pattern:

- `app/llm/base_provider.py` declares `generate(messages, temperature,
  max_tokens, json_mode)`. `GroqProvider` implements it; `get_llm_provider()`
  selects one from configuration. No service imports Groq directly.
- `app/search/base_provider.py` does the same for web search, currently
  implemented by SearXNG.

The value is not hypothetical. When Groq's server-side JSON validator rejects a
generation it raises a provider-specific `BadRequestError`; `GroqProvider`
translates that into a plain `ValueError`, so the retry logic in
`app/llm/structured.py` handles provider rejections and parse failures through
one path and stays provider-agnostic.

### 2.1.2 High-level architecture

![](../screenshots/fig-2.1-architecture.png)

> **Figure 2.1 — System Architecture.** Source:
> `docs/diagrams/architecture.mmd`

The figure separates the personalization subsystem from the general service
layer, because that subsystem is the project's substance. Four components
cooperate on every generated response:

- **Prompt Builder** (`app/llm/prompt_builder.py`) assembles the system prompt
  from modular blocks — tutor persona, learner memory, adaptation instructions
  derived from the profile, and retrieved reference material.
- **RAG Retriever** (`app/rag/retriever.py`) embeds the query and finds the
  nearest stored explanations by cosine distance.
- **Response Parser** (`app/llm/response_parser.py`) recovers structured output
  from imperfect model responses.
- **Personalization Reasons** (`app/llm/personalization_reasons.py`) records
  which signals were applied, for display to the learner.

### 2.1.3 Data flow

![](../screenshots/fig-2.2a-dfd-level-0.png)

> **Figure 2.2a — Data Flow Diagram, Level 0.** Source:
> `docs/diagrams/dfd-level-0.mmd`

![](../screenshots/fig-2.2b-dfd-level-1.png)

> **Figure 2.2b — Data Flow Diagram, Level 1.** Source:
> `docs/diagrams/dfd-level-1.mmd`

The level-1 diagram decomposes the platform into six processes over eight data
stores. Two flows carry most of the system's character.

**Process 3.0, conducting a tutoring session,** reads from three stores before
calling the model: the learner profile and accumulated memory, mastery-derived
strengths and weaknesses, and vector-retrieved reference chunks. That
convergence is what distinguishes a personalized explanation from a generic one.

**Process 6.0, evolving the learner profile,** closes the loop. Conversation
history is summarised by the model into an updated learner memory, which feeds
process 3.0 on the next turn. The system's knowledge of the learner is therefore
a function of every prior session, not just the current one.

### 2.1.4 Component interaction

![](../screenshots/fig-2.3-component-interaction.png)

> **Figure 2.3 — Component Interaction.** Source:
> `docs/diagrams/component-interaction.mmd`

Most routes follow one router → one service → one repository. Two are
deliberately wider:

`ChatService` composes `LearnerProfileService` and `EngagementService` in
addition to its own repository, because producing one reply requires profile
data, retrieval and event tracking together.

`QuizService` fans out furthest. Submitting a single answer updates topic
progress, concept mastery, the spaced-repetition schedule and the engagement
log. Keeping that orchestration in one service — rather than spreading it
across the router and several repositories — means the ordering constraint
(mastery must be updated before SM-2 reads it, since scheduling depends on the
new mastery level) is expressed in one readable place.

### 2.1.5 Database design

![](../screenshots/fig-2.4-er-model.png)

> **Figure 2.4 — Entity-Relationship Model.** Source:
> `docs/diagrams/er-model.mmd`

Thirteen tables. All inherit `BaseEntity`, giving every row a UUID primary key
and `created_at` / `updated_at` timestamps. UUIDs rather than sequential
integers avoid exposing record counts and make identifiers non-guessable, which
matters given how many endpoints accept an id from the client.

Design points worth noting:

**Mastery is a state row, not an event log.** `concept_mastery` carries a
composite unique constraint on `(user_id, concept_node_id)`. Each learner has
exactly one mastery row per concept, updated in place. The full history lives in
`quiz_attempts` and `engagement_events` if it is ever needed, but the read path
that matters — "what does this learner know?" — is a single indexed lookup.

**Prerequisites are typed edges, not a fixed ordering.** `concept_edges` has a
`relation_type` of `PREREQUISITE`, `RELATED` or `EXTENDS`. Only `PREREQUISITE`
gates unlocking; the others exist to inform recommendation and are available to
the interface. A single edge table serves both directions, with two
relationships defined on `ConceptNode` distinguished by foreign key.

**JSONB where the shape is genuinely variable.** `metadata_json` on
`chat_messages` holds a quiz reference for quiz messages and a personalization
snapshot for assistant messages. `payload_json` on `engagement_events` differs
per event type. Both would otherwise require either a wide sparse table or a
join per message.

**Engagement survives deletion.** Deleting a chat session removes its messages,
quizzes, attempts and feedback in foreign-key-safe order, but *nulls* the
session reference on `engagement_events` rather than deleting them. A learner
who deletes a session should not lose their study streak.

**Vector storage is co-located.** `content_embeddings.embedding` is a
`vector(384)` column in the same PostgreSQL instance as the relational data,
not a separate vector database. At this scale a dedicated vector store would
add an operational dependency and a consistency problem for no benefit;
pgvector's cosine-distance operator over a few hundred rows is more than
sufficient.

### 2.1.6 Runtime sequences

Two flows are given as sequence diagrams because their ordering constraints
matter and are not evident from the static structure.

![](../screenshots/fig-2.5-sequence-chat.png)

> **Figure 2.5 — Sequence, a personalized chat turn.** Source:
> `docs/diagrams/sequence-chat.mmd`

![](../screenshots/fig-2.6-sequence-quiz-mastery.png)

> **Figure 2.6 — Sequence, quiz submission through mastery and SM-2.** Source:
> `docs/diagrams/sequence-quiz-mastery.mmd`

Figure 2.5 shows the three personalization sources converging before the model
is called. Figure 2.6 shows why mastery must be updated before SM-2 runs: the
recall-quality mapping reads the *new* mastery level to decide between quality
4 and quality 5.

## 2.2 Technology Stack

### 2.2.1 Languages

| Language | Where | Why |
|---|---|---|
| Python 3.11 | Backend | Strongest ecosystem for LLM and embedding work; `X \| None` union syntax and native `list[str]` generics keep signatures readable |
| JavaScript (ES2022) | Frontend | Plain JSX without TypeScript, per project constraints |
| SQL | Migrations, vector queries | Cosine-distance ordering is expressed directly |

### 2.2.2 Backend frameworks and libraries

| Library | Role | Rationale |
|---|---|---|
| FastAPI | Web framework | Dependency injection gives clean per-request database sessions and an authentication dependency reused across every protected route; generates OpenAPI documentation from the DTOs |
| Pydantic v2 | Validation, serialisation | Request validation at the boundary — an invalid signup never reaches a service; response models make the API contract explicit and machine-checkable |
| SQLAlchemy 2.0 | ORM | Declarative models with typed relationships; the repository layer confines it so services stay persistence-agnostic |
| Alembic | Migrations | Versioned, reviewable schema changes. Three migrations to date |
| pgvector | Vector similarity | Keeps embeddings beside relational data; exposes `cosine_distance` through the SQLAlchemy type |
| sentence-transformers | Embeddings | `all-MiniLM-L6-v2` runs locally: no per-embedding API cost, no data leaving the deployment, 384 dimensions is a good size/quality trade |
| groq | LLM client | Fast inference on the free tier; supports server-side JSON mode |
| python-jose | JWT | Signing and verification with expiry |
| bcrypt | Password hashing | Deliberate slowness and per-password salting |
| httpx | HTTP client | Used by the SearXNG provider |

### 2.2.3 Frontend frameworks and libraries

| Library | Role | Rationale |
|---|---|---|
| React 19 | UI | Component model suits a stateful chat interface; hooks cover all state needs without a store library |
| Vite 5 | Build tool | Fast dev server; `import.meta.env` handles build-time configuration |
| React Router 7 | Routing | Nine routes; URL-driven state means the selected session and concept survive refresh and are shareable |
| Tailwind CSS 3 | Styling | Utility classes keep styling colocated with markup; responsive breakpoints handle the mobile sidebar |
| react-markdown | Rendering | Renders tutor output; raw HTML disabled by default, which matters when displaying model-generated content |
| rehype-highlight | Code highlighting | Syntax highlighting inside markdown code fences |
| react-hot-toast | Notifications | Non-blocking error feedback |

Deliberately **not** used: a state-management library (Context plus local state
is sufficient at nine routes), and a data-fetching library (the two custom hooks
in `useApi.js` cover the needed cases in 76 lines).

### 2.2.4 Tools and platforms

| Tool | Purpose |
|---|---|
| Docker Compose | Runs database, backend and search with one command |
| PostgreSQL 15 (pgvector image) | Relational and vector storage |
| SearXNG | Self-hosted meta-search for reference lookup |
| Git and GitHub | Version control; three contributors |
| GitHub Actions | Five-job CI pipeline |
| ruff | Python linting |
| pytest | Backend testing, with coverage |
| Vitest, React Testing Library | Frontend testing |
| ESLint | JavaScript linting, including React hook rules |
| CodeQL | Static application security testing |
| pip-audit | Dependency vulnerability scanning |
| Trivy | Container image scanning |
| Render, Vercel | Cloud hosting for backend and frontend |

## 2.3 System Modules

### 2.3.1 Authentication

**Files:** `routers/auth_router.py`, `services/auth_service.py`,
`utils/security.py`, `utils/auth_middleware.py`

Sign-up hashes with bcrypt — per-password salt, deliberately slow — and issues a
24-hour HS256 JWT carrying the user id as `sub`. `get_current_user` is a FastAPI
dependency that decodes the token, loads the user, and raises 401 on any
failure; every protected route declares it, so no route can accidentally omit
authentication.

Login answers the same "Invalid email or password" whether the address is
unknown or the password wrong, so the endpoint cannot be used to enumerate
registered accounts.

### 2.3.2 Learner profile and personalization

**Files:** `services/learner_profile_service.py`,
`llm/prompt_builder.py`, `llm/personalization_reasons.py`

Holds explicit preferences and derived state. `get_personalization_context`
assembles the dictionary consumed by the prompt builder: preferences, plus
strengths (mastery ≥ 0.7) and weaknesses (mastery < 0.4 with at least one
answer recorded), plus the accumulated learner memory.

That memory is the module's distinguishing feature. Every five messages,
`maybe_update_summary` sends recent conversation together with the existing
summary and asks the model to *evolve* rather than replace it, explicitly
instructing that newer evidence wins where the two conflict. Failures are caught
and logged: a summarisation error must never cost the learner their reply.

### 2.3.3 Knowledge graph

**Files:** `services/knowledge_graph_service.py`,
`repositories/knowledge_graph_repo.py`, `data/dsa_graph.json`,
`data/seed_graph.py`

Twenty-five concepts across five tiers with thirty-seven typed edges, seeded
from JSON. Provides the mastery-overlaid graph the dashboard renders, the
unlocked set (all prerequisites at or above 0.6), and the next-concept
recommendation — lowest mastery first, then easiest tier.

Mastery updates blend rather than replace: 70% observed accuracy, 30% prior
mastery. One unlucky answer therefore cannot erase an established history, while
a genuine change in performance still moves the score within a few attempts.

### 2.3.4 Chat and tutoring

**Files:** `services/chat_service.py`, `routers/chat_router.py`

Owns session lifecycle and message exchange. Session creation runs the model
*before* persisting anything, so a generation failure leaves no orphan session
behind. Long conversations are compacted: past twenty messages the service
substitutes a generated summary plus the ten most recent turns, holding token
use roughly constant as a session grows.

### 2.3.5 Quiz and assessment

**Files:** `services/quiz_service.py`, `routers/quiz_router.py`

Generates one multiple-choice question at a time, targeted at the learner's
recorded weak areas where any exist. Grading is server-side; the answer key,
hint and explanation are withheld from the client until an attempt is recorded.
Submission fans out to topic progress, concept mastery, SM-2 rescheduling and
the engagement log.

### 2.3.6 Spaced repetition

**Files:** `services/spaced_repetition_service.py`, `routers/review_router.py`

Implements SM-2 over quiz outcomes. Detailed in section 2.4.

### 2.3.7 Retrieval-augmented generation

**Files:** `rag/embedder.py`, `rag/indexer.py`, `rag/retriever.py`,
`rag/content_seeder.py`

The seeder generates beginner, intermediate and advanced explanations for each
concept and embeds them. At query time the retriever embeds the learner's
question and returns the nearest chunks, optionally filtered by concept.

The embedder degrades deliberately: if `sentence-transformers` is not
installed, `is_available()` returns false, the retriever returns an empty list,
and the prompt builder simply omits the reference block. The tutor continues on
profile and conversation history alone. This is what makes the slim cloud image
viable.

### 2.3.8 Onboarding

**Files:** `services/onboarding_service.py`, `routers/onboarding_router.py`

Ten fixed placement questions spanning tiers one to four — fixed rather than
generated, so placement is consistent between learners and costs no LLM call.
Each question maps to concepts; per-concept accuracy seeds initial mastery,
capped at 0.6 because a placement quiz is weak evidence, with confidence set to
0.2 to record that explicitly.

### 2.3.9 Functional flow

A complete learner journey:

1. **Sign up** → account created, JWT issued
2. **Onboarding step 1** → preferences saved to the profile
3. **Onboarding step 2** → placement quiz seeds mastery across the graph
4. **Dashboard** → concepts by tier, mastery bars, locks on unmet
   prerequisites, recommended next concept, progress summary
5. **Start a session** → opening explanation generated, shaped by profile and
   grounded in retrieved material
6. **Converse** → each reply personalized; memory revised every five messages
7. **Take a quiz** → question targets weak areas; grading updates mastery
8. **Mastery crosses 0.6** → dependent concepts unlock on the dashboard
9. **SM-2 schedules review** → concept reappears in the review queue when due
10. **Return later** → tutor recalls prior sessions through accumulated memory

{{PAGEBREAK}}
