# CHAPTER 5: PROJECT EXECUTION EVIDENCE

## 5.1 Version Control Evidence

**Repository:** {{github_url}}

| Metric | Value |
|---|---|
| Total commits | 65 |
| Contributors | 3 |
| Development window | 14 April – 11 August 2026 (18 weeks) |
| Weeks with at least one commit | 18 of 18 |
| Lines of application code | ~9,900 |
| Backend endpoints | 24 |
| Database tables | 13 |
| Migrations | 3 |
| Automated tests | 133 |

### 5.1.1 Contribution by member

| Member | Role | Commits | Main areas |
|---|---|---|---|
| Suraj | AI/ML | 19 | LLM integration, RAG pipeline, prompt engineering, chat and quiz services, personalization transparency |
| Sandip Dey | Platform and full-stack | 21 | Data model, migrations, knowledge graph, spaced repetition, onboarding, Docker, deployment, dashboard and review pages |
| Udit Nayak | Backend API and QA | 25 | Authentication and security, repositories, routers, DTOs, the test suite, CI pipeline, auth and profile pages |

All three of us worked on both backend and frontend. We split by concern rather
than by layer, so each person owned the interface for their own backend work.
That kept the number of handoffs low.

### 5.1.2 Commit conventions

We used Conventional Commits throughout, with a scope where one applied:
`feat(chat):`, `fix(security):`, `refactor(api):`, `perf(graph):`, `test:`,
`docs(report):`, `ci:`, `build:` and `chore:`.

Commit bodies explain why rather than restating the diff. Where a commit fixes a
bug it names the failure and, where relevant, why it went unnoticed. The commit
fixing the hook-order violations, for example, records that the ESLint rule was
enabled from the start but never run in CI.

### 5.1.3 Repository screenshots

![](../screenshots/fig-5.1-commit-history.png)

> **Figure 5.1 — Commit history.** Distribution of commits across the
> development window.

![](../screenshots/fig-5.2-contributors.png)

> **Figure 5.2 — Contributor activity.** GitHub Insights view showing all three
> members.

## 5.2 Weekly Progress Summary

| Week | Dates | Task Planned | Task Completed | Supervisor Remark |
|---|---|---|---|---|
| 1 | 14–19 Apr | Scaffolding, database design, auth | Docker Compose stack, Alembic, 13-table schema, JWT auth with bcrypt | |
| 2 | 20–26 Apr | LLM layer, reference search | Provider abstraction with Groq, prompt builder, response parser, SearXNG provider | |
| 3 | 27 Apr – 3 May | Frontend foundation | Vite, React and Tailwind scaffold; AuthContext, protected routes, login and signup | |
| 4 | 4–10 May | Knowledge graph and RAG models | Concept node, edge and mastery models; learner profile; embedding table | |
| 5 | 11–17 May | Retrieval and learning services | Local embedder, indexer, retriever; graph, onboarding and SM-2 services | |
| 6 | 18–24 May | Tutoring and assessment | Chat service with personalized prompts and RAG grounding; quiz generation and grading | |
| 7 | 25–31 May | Chat and onboarding UI | Chat page with sidebar and markdown; three-step onboarding with placement quiz | |
| 8 | 1–7 Jun | Dashboard | Tiered concept grid with mastery bars and locks; detail panel; recommendation card | |
| 9 | 8–14 Jun | Transparency, review, profile | "Why this response" note; review page; profile editing; README; first tests and CI | |
| 10 | 15–21 Jun | Security review | Four access control bugs found and fixed; quiz answers withheld until submission | |
| 11 | 22–28 Jun | Correctness fixes | Two React hook-order bugs; pgvector extension migration; migrate-and-seed entrypoint | |
| 12 | 29 Jun – 5 Jul | Docs and performance | Setup instructions corrected; two N+1 queries removed; retry logic extracted | |
| 13 | 6–12 Jul | API contract | Response models on all endpoints; study streak; analytics on the dashboard; authorization tests | |
| 14 | 13–19 Jul | Frontend testing | Vitest harness; API client, quiz card, message bubble and hooks covered; smoke test extended | |
| 15 | 20–26 Jul | Pipeline and deployment | Frontend lint and tests in CI; production image; Render blueprint; Vercel config | |
| 16 | 27 Jul – 2 Aug | Diagrams and runbook | Deployment runbook; architecture, DFD, ER and sequence diagrams | |
| 17 | 3–9 Aug | Report chapters 1–5 | Front matter, introduction, implementation, algorithms, testing, deployment | |
| 18 | 10–11 Aug | Report completion | Conclusion, references, appendices, report generator, screenshot guide; migrated to a current Groq model after the previous one was retired upstream | |

Weeks 1 to 9 were feature building and weeks 10 to 18 were hardening, testing
and documentation. The second phase added almost no new user-facing features.
The two exceptions were the study streak and the progress panel, which were
already built on the backend but had never been connected to the interface.

## 5.3 Supervisor Interaction Summary

| # | Date | Topics Discussed | Key Feedback Received | Action Taken |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |

*Summary of guidance to be completed.*

{{PAGEBREAK}}
