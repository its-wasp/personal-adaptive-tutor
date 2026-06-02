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
```

Create a `.env` file in the project root:
```env
POSTGRES_DB=adaptive_learning
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DATABASE_URL=postgresql://postgres:postgres@db:5432/adaptive_learning

GROQ_API_KEY=your_groq_api_key
JWT_SECRET=your_jwt_secret

SEARXNG_URL=http://searxng:8080
```

### 2. Start backend services
```bash
docker compose up
```
This starts PostgreSQL (with pgvector), the FastAPI backend, and SearXNG.

### 3. Start frontend
```bash
cd frontend
npm install
npm run dev
```

### 4. Open in browser
Navigate to `http://localhost:5173`. Sign up, complete onboarding, and start learning.

## CRUD Operations

| Operation | Where | API Endpoint |
|-----------|-------|-------------|
| **Create** | New chat session, send message, submit quiz | `POST /chat/create`, `POST /chat/message`, `POST /quiz/submit` |
| **Read** | Dashboard graph, conversations, review queue, profile | `GET /graph/dsa`, `GET /chat/{id}/conversation`, `GET /review/due`, `GET /profile/me` |
| **Update** | Edit learning preferences | `PUT /profile/me/preferences` |
| **Delete** | Delete chat session | `DELETE /chat/{id}` |
