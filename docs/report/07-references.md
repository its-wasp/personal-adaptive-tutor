# REFERENCES

[1] B. S. Bloom, "The 2 Sigma Problem: The Search for Methods of Group
Instruction as Effective as One-to-One Tutoring," *Educational Researcher*,
vol. 13, no. 6, pp. 4–16, Jun. 1984.

[2] P. A. Woźniak and E. J. Gorzelańczyk, "Optimization of repetition spacing in
the practice of learning," *Acta Neurobiologiae Experimentalis*, vol. 54, no. 1,
pp. 59–62, 1994.

[3] OWASP Foundation, "OWASP Top 10:2021 — A01 Broken Access Control," 2021.
[Online]. Available: https://owasp.org/Top10/A01_2021-Broken_Access_Control/
[Accessed: Jul. 2026].

[4] P. Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP
Tasks," in *Advances in Neural Information Processing Systems 33*, 2020,
pp. 9459–9474.

[5] N. Reimers and I. Gurevych, "Sentence-BERT: Sentence Embeddings using
Siamese BERT-Networks," in *Proc. EMNLP-IJCNLP*, Hong Kong, 2019,
pp. 3982–3992.

[6] J. Dunlosky, K. A. Rawson, E. J. Marsh, M. J. Nathan and D. T. Willingham,
"Improving Students' Learning With Effective Learning Techniques,"
*Psychological Science in the Public Interest*, vol. 14, no. 1, pp. 4–58, 2013.

[7] N. Provos and D. Mazières, "A Future-Adaptable Password Scheme," in *Proc.
USENIX Annual Technical Conference*, Monterey, CA, 1999, pp. 81–91.

[8] M. Jones, J. Bradley and N. Sakimura, "JSON Web Token (JWT)," RFC 7519,
IETF, May 2015. [Online]. Available:
https://datatracker.ietf.org/doc/html/rfc7519

[9] T. H. Cormen, C. E. Leiserson, R. L. Rivest and C. Stein, *Introduction to
Algorithms*, 4th ed. Cambridge, MA: MIT Press, 2022.

[10] S. Ramírez, "FastAPI Documentation." [Online]. Available:
https://fastapi.tiangolo.com/ [Accessed: Aug. 2026].

[11] Meta Open Source, "React Documentation." [Online]. Available:
https://react.dev/ [Accessed: Aug. 2026].

[12] SQLAlchemy Project, "SQLAlchemy 2.0 Documentation." [Online]. Available:
https://docs.sqlalchemy.org/en/20/ [Accessed: Aug. 2026].

[13] A. Kane, "pgvector: Open-source vector similarity search for Postgres."
[Online]. Available: https://github.com/pgvector/pgvector [Accessed: Aug. 2026].

[14] Groq Inc., "Groq API Documentation." [Online]. Available:
https://console.groq.com/docs [Accessed: Aug. 2026].

[15] Hugging Face, "sentence-transformers/all-MiniLM-L6-v2 Model Card."
[Online]. Available:
https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
[Accessed: Aug. 2026].

[16] PostgreSQL Global Development Group, "PostgreSQL 15 Documentation."
[Online]. Available: https://www.postgresql.org/docs/15/ [Accessed: Aug. 2026].

[17] Vitest Contributors, "Vitest Documentation." [Online]. Available:
https://vitest.dev/ [Accessed: Aug. 2026].

[18] Conventional Commits, "Conventional Commits 1.0.0." [Online]. Available:
https://www.conventionalcommits.org/en/v1.0.0/ [Accessed: Aug. 2026].

{{PAGEBREAK}}

# APPENDIX

## Appendix A — User Manual

### Getting started

Select **Sign up** and provide a name, email and password. You are signed in
straight away and taken to onboarding.

**Step 1, preferences.** Four questions decide how the tutor writes to you:

| Setting | Options | What it changes |
|---|---|---|
| Learning style | Visual, Reading, Example-first, Theory-first | Whether explanations open with a diagram, prose, a worked example or the concept |
| Pace | Quick, Moderate, Detailed | How much detail per step |
| Explanation detail | Concise, Standard, Verbose | Overall length |
| Analogies | On or off | Whether real-world comparisons are used |

None of these are permanent. You can change them on the Profile page and they
take effect from your next message.

**Step 2, placement quiz.** Ten multiple-choice questions from foundational to
advanced. Answer honestly. The point is to calibrate the starting level, not to
score you, and guessing well only means the tutor starts you further ahead than
you are ready for. You can move between questions before submitting.

**Step 3, results.** Your score and starting level. The knowledge graph is
seeded from your per-concept performance.

### The dashboard

All 25 concepts appear in five tiers from Foundations to Expert.

Each card shows the concept name, a short description, a mastery bar and any
prerequisites. The bar is grey when untouched, red below 40%, amber below 75%
and green above that.

A padlock means a prerequisite is below 60% mastery. You can still open a locked
concept and the tutor will assume the foundation is missing.

**Recommended next** suggests your weakest unlocked concept, easiest tier first
where there is a tie. **Your progress** shows points, accuracy and your
strongest topic. The **Review** badge turns amber with a count when concepts are
due.

### Learning in a session

Click a concept and choose **Start session**, or go to **Sessions** and click
**+ New** for a free topic. Concept-linked sessions update your mastery graph;
free topics only accumulate points.

Type a question and press Enter. Shift+Enter adds a newline. Responses render as
markdown with highlighted code. The first response takes a few seconds.

Under each tutor message is a small **Why this response** link. Expanding it
shows which signals shaped that reply: your learning style, concepts you have
struggled with, memory from earlier sessions, and how many reference
explanations were used.

Click **Generate quiz** at any point. Questions target your weak areas where you
have any. Pick an option and submit, and the answer, an explanation and a hint
if you were wrong are revealed. Correct answers in a concept-linked session
raise mastery and push the next review further out. Wrong answers bring it back
tomorrow.

The sidebar lists your sessions. Hover to reveal the delete control. Deleting
removes the conversation and its quizzes but leaves your points, mastery and
streak alone.

### Review

The Review page lists concepts due for revision, most overdue first, with
mastery, interval and last review date. **Start review** opens a session pinned
to that concept. The schedule updates when you answer a quiz in that session,
not when you open the page.

### Profile

Shows sessions completed, streak, strong and weak areas, the tutor's memory of
how you learn, and your editable preferences.

### Troubleshooting

| Problem | What to do |
|---|---|
| "Tutor is thinking…" for a long time | Normal is 2–6 seconds. Past 30 seconds the hosted service is probably waking from idle |
| "Couldn't parse the response" | A transient model fault, send the message again |
| Dashboard shows no concepts | The graph was not seeded, see Appendix B |
| Signed out unexpectedly | Sessions last 24 hours |
| Streak shows 0 despite studying | One full missed day resets it |

## Appendix B — Installation Guide

**Prerequisites:** Docker Desktop running, Node.js 18+, and a free Groq API key
from console.groq.com.

```bash
# 1. Clone and configure
git clone https://github.com/its-wasp/personal-adaptive-tutor.git
cd personal-adaptive-tutor
cp .env.example .env
#    edit .env: set GROQ_API_KEY and JWT_SECRET

# 2. Start the backend stack
docker compose up
#    wait for "Application startup complete"
#    migrations and graph seeding run automatically

# 3. Start the frontend in a second terminal
cd frontend
npm install
npm run dev

# 4. Open http://localhost:5173
```

Verify:

```bash
curl http://localhost:8000/health        # {"status":"ok"}
curl http://localhost:8000/health/db     # {"status":"ok","database":"connected"}
python backend/scripts/smoke_test.py
```

API documentation is at http://localhost:8000/docs.

Optionally seed RAG content, which takes about ten minutes:

```bash
docker compose exec backend python -m app.rag.content_seeder
```

Run the tests:

```bash
cd backend  && pytest -v --cov=app
cd frontend && npm test
```

**Common problems:**

| Symptom | Fix |
|---|---|
| `type "vector" does not exist` | Not the pgvector image. `docker compose down -v` and start again |
| Dashboard empty after signup | Seeding did not run. Check `[entrypoint]` lines in the logs |
| Port 5432 already allocated | A local Postgres is running. Stop it or change the host port |
| Chat returns 502 | `GROQ_API_KEY` missing or invalid |
| Frontend cannot reach the API | Check the backend is up and `VITE_API_URL` matches |

## Appendix C — Source Code

**Repository:** {{github_url}}

```
personal-adaptive-tutor/
├── backend/
│   ├── app/
│   │   ├── models/          SQLAlchemy models (13 tables)
│   │   ├── repositories/    Data access
│   │   ├── services/        Business logic
│   │   ├── routers/         24 REST endpoints
│   │   ├── dtos/            Request and response schemas
│   │   ├── llm/             Provider, prompts, parsing
│   │   ├── rag/             Embedding, indexing, retrieval
│   │   └── data/            Knowledge graph seed
│   ├── alembic/             Migrations
│   ├── tests/               81 unit tests
│   └── scripts/             End-to-end smoke test
├── frontend/
│   └── src/
│       ├── pages/           7 route components
│       ├── components/      Chat, graph, dashboard, shared
│       ├── context/         Auth state
│       ├── hooks/           useAuth, useApi
│       └── lib/             API client
├── docs/
│   ├── report/              This report
│   ├── diagrams/            Mermaid sources for all figures
│   └── deployment.md        Operational runbook
├── docker-compose.yaml
├── render.yaml
└── .github/workflows/ci.yml
```

## Appendix D — Demonstration Video

**URL:** {{demo_video_url}}

Contents:

1. Signup and onboarding, including the placement quiz
2. Dashboard: tiers, mastery, locks and the recommendation
3. A tutoring session with "Why this response" expanded
4. Quiz generation, submission and the mastery change
5. The review queue under the SM-2 schedule
6. Profile page showing the tutor's memory
7. The same concept explained under two different learner profiles, side by
   side
