# Adaptive Learning Platform — Personal AI Tutor for DSA

An AI-powered study companion that delivers **personalized tutoring** for Data Structures & Algorithms. Unlike generic chatbots, this platform builds a learner profile over time — remembering how you think, what you struggle with, and how you prefer to learn — so every explanation feels like it was written specifically for you.

## Problem Statement

**Who is the user?**
College students studying Data Structures & Algorithms, and self-learners looking for a structured, personalized curriculum.

**What problem does it solve?**
Existing learning platforms (Brilliant, Codecademy, YouTube) deliver the same explanation to every learner. If you're a visual learner who needs examples before theory and struggles with recursion, you get the same content as someone who prefers formal definitions and breezes through recursion. This platform closes that gap with deep personalization — adaptive difficulty, learner memory, and retrieval-augmented explanations grounded in reference material.

**Why does it matter?**
Personalized tutoring produces significantly better outcomes than one-size-fits-all content. This platform aims to approximate the experience of a 1-on-1 tutor who remembers you across sessions.

## Features

### Core Learning Experience
- **Conversational tutor** — chat-based sessions with an AI tutor that explains DSA concepts using markdown, code blocks, and inline quizzes
- **Knowledge graph** — 25+ DSA concepts organized into 5 difficulty tiers (Foundations → Expert) with prerequisite dependencies
- **Inline quizzes** — MCQ quizzes generated on-demand, with correct-answer reveal, explanations, and a "Next question" flow
- **Concept-linked sessions** — start a session from any concept on the dashboard; quiz results update mastery on the graph

### Personalization Engine
- **Learner profile** — captures learning style (Visual / Reading / Example-first / Theory-first), pace, detail level, code complexity preference, and analogy toggle
- **Evolving tutor memory** — the tutor builds a natural-language summary of how you learn, updated every 5 messages, and uses it in every response
- **RAG pipeline** — retrieves relevant reference explanations via pgvector embeddings and grounds the LLM's output in them
- **"Why this response" pill** — expandable indicator under each assistant message showing which profile signals shaped it (e.g., "Example-first", "Extra care on Recursion", "Remembered you")
- **Strengths & weaknesses** — derived from mastery data and injected into prompts so the tutor builds on what you know and slows down on what's hard

### Spaced Repetition
- **SM-2 algorithm** — quiz results update review schedules (correct → interval grows, incorrect → see it tomorrow)
- **Review queue** — dedicated page showing overdue concepts with mastery bars, intervals, and "Start review" buttons
- **Dashboard badge** — amber "Review (N)" badge when concepts are due

### Onboarding
- **3-step flow** — preference selection → 10-question placement quiz → results with initial mastery assessment
- **Placement quiz** — seeds initial mastery levels across the knowledge graph so the tutor calibrates from day one

### Profile & Settings
- **Editable preferences** — change learning style, pace, detail level, code complexity, and analogies at any time
- **Tutor memory view** — read-only card showing what the tutor has learned about you
- **Mastery highlights** — strengths (green) and weak areas (amber) at a glance

## Tech Stack

### Frontend
- **React 19** (Vite 5) — plain JSX, no TypeScript
- **React Router 7** — client-side routing with URL-driven state
- **Tailwind CSS 3** — utility-first styling, responsive breakpoints
- **react-hot-toast** — toast notifications
- **react-markdown + rehype-highlight** — markdown rendering with syntax-highlighted code blocks

### Backend
- **FastAPI** (Python) — async REST API
- **PostgreSQL 15** (pgvector) — relational storage + vector similarity search
- **SQLAlchemy + Alembic** — ORM + migrations
- **Groq** (LLaMA 3.1 8B) — LLM provider with JSON mode and structured output
- **sentence-transformers** (all-MiniLM-L6-v2) — local embeddings for RAG (384-dim vectors)
- **SearXNG** — meta-search for reference material

### Infrastructure
- **Docker Compose** — single command to run all services (db, backend, searxng)
- **JWT authentication** — stateless auth with bearer tokens

## React Concepts Demonstrated

### Core
- Functional components (all 20+ components)
- Props and component composition (SessionList, MessageBubble, ConceptGrid, QuizCard)
- `useState` for local state (Chat: 7 state variables, Onboarding: 9, QuizCard: 4)
- `useEffect` with varied dependency arrays (conversation fetch, scroll behavior, placement quiz loading, profile hydration)
- Conditional rendering (ternary, &&, early return patterns)
- Lists with keys (messages, sessions, concept cards, quiz options, review cards)

### Intermediate
- Lifting state up (Dashboard → ConceptGrid/ConceptDetail, Chat → SessionList/MessageBubble)
- Controlled components (ChatInput, Login/Signup forms, Onboarding preferences, Profile preferences, NewSessionModal)
- React Router (9 routes, `useParams`, `useNavigate`, `useSearchParams`)
- Context API (`AuthContext` providing user, profile, login, logout, refreshProfile across the app)

### Advanced
- `useMemo` (locked concept sets, tier grouping, active session lookup, context value memoization)
- `useCallback` (event handlers in Chat, Dashboard; API hooks)
- `useRef` (scroll container, message anchor pinning, auto-grow textarea, stale-response guard)
- `React.lazy` + `Suspense` (NewSessionModal code-split)
- `React.memo` (MessageBubble — prevents full list re-render on new message)

## Project Structure

```
adaptive-learning-v1/
├── frontend/
│   └── src/
│       ├── pages/              # Route-level components
│       │   ├── Login.jsx
│       │   ├── Signup.jsx
│       │   ├── Onboarding.jsx
│       │   ├── Dashboard.jsx
│       │   ├── Chat.jsx
│       │   ├── Review.jsx
│       │   └── Profile.jsx
│       ├── components/
│       │   ├── chat/           # SessionList, MessageBubble, QuizCard, ChatInput, NewSessionModal
│       │   ├── graph/          # ConceptGrid, ConceptDetail
│       │   ├── dashboard/      # RecommendedNext
│       │   └── shared/         # MarkdownRenderer, ProtectedRoute
│       ├── context/            # AuthContext
│       ├── hooks/              # useAuth, useApi (useApiGet, useApiMutation)
│       ├── lib/                # api.js (fetch wrapper with JWT)
│       ├── App.jsx             # Router setup
│       └── main.jsx            # Entry point
├── backend/
│   └── app/
│       ├── models/             # SQLAlchemy models (User, ChatSession, ChatMessage, Quiz, ConceptNode, LearnerProfile, etc.)
│       ├── routers/            # FastAPI route handlers
│       ├── services/           # Business logic (ChatService, QuizService, LearnerProfileService, etc.)
│       ├── repositories/       # Database queries
│       ├── dtos/               # Pydantic request/response schemas
│       ├── llm/                # LLM provider, prompt builder, response parser, personalization reasons
│       ├── rag/                # Embedder, retriever, indexer
│       └── data/               # DSA graph seed data
├── docker-compose.yaml
└── README.md
```

## Setup Instructions

### Prerequisites
- Docker Desktop (running)
- Node.js 18+

### 1. Clone and configure
```bash
git clone https://github.com/its-wasp/personal-adaptive-tutor.git
cd personal-adaptive-tutor
cp .env.example .env
```

Then edit `.env` and set at minimum:

| Variable | Notes |
|---|---|
| `GROQ_API_KEY` | Required. Free key from [console.groq.com](https://console.groq.com). Without it, chat and quiz generation fail. |
| `JWT_SECRET` | Any long random string. |

The Postgres and SearXNG defaults in `.env.example` work as-is for local Docker.
For a cloud database, set `DATABASE_URL` instead of the individual `POSTGRES_*`
variables — it takes precedence when present (see `backend/app/config.py`).

### 2. Start backend services
```bash
docker compose up
```

This starts PostgreSQL (with pgvector), the FastAPI backend, and SearXNG. On
first boot the backend entrypoint automatically:

1. waits for Postgres to accept connections,
2. runs `alembic upgrade head` (creates the `vector` extension and all 13 tables),
3. seeds the 25-concept DSA knowledge graph.

Steps 2 and 3 are idempotent, so later starts are no-ops. Watch for
`[entrypoint]` lines in the logs to confirm. Wait for
`Application startup complete` before using the app.

Verify with:
```bash
curl http://localhost:8000/health/db     # {"status":"ok","database":"connected"}
```

### 3. Start frontend
```bash
cd frontend
npm install
npm run dev
```

### 4. Open in browser
Navigate to `http://localhost:5173`. Sign up, complete onboarding, and start learning.

### 5. Optional — seed RAG reference content
The tutor works without this (it falls back to personalization plus conversation
history), but grounding improves noticeably with it. Generates three explanation
variants per concept via the LLM and embeds them into pgvector:

```bash
docker compose exec backend python -m app.rag.content_seeder
```

Takes roughly 10 minutes for all 25 concepts — it sleeps between calls to stay
inside Groq's free-tier rate limit. Safe to interrupt and re-run.

### Running without Docker
If you'd rather run the backend directly, the entrypoint's work has to be done
by hand:

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
python -m app.data.seed_graph
uvicorn app.main:app --reload
```

## CRUD Operations

| Operation | Where | API Endpoint |
|-----------|-------|-------------|
| **Create** | New chat session, send message, submit quiz | `POST /chat/create`, `POST /chat/message`, `POST /quiz/submit` |
| **Read** | Dashboard graph, conversations, review queue, profile | `GET /graph/dsa`, `GET /chat/{id}/conversation`, `GET /review/due`, `GET /profile/me` |
| **Update** | Edit learning preferences | `PUT /profile/me/preferences` |
| **Delete** | Delete chat session | `DELETE /chat/{id}` |
