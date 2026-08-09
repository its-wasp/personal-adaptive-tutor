# CHAPTER 5: PROJECT EXECUTION EVIDENCE

## 5.1 Version Control Evidence

### 5.1.1 Repository

**URL:** {{github_url}}

**Default branch:** `main`

**Contributors:** 3

### 5.1.2 Commit statistics

| Metric | Value |
|---|---|
| Total commits | 59 |
| Contributors | 3 |
| Development window | 14 April – 10 August 2026 (18 weeks) |
| Weeks with at least one commit | 18 of 18 |
| Source files | 130+ |
| Lines of application code | ~9,900 |
| Backend endpoints | 24 |
| Database migrations | 3 |
| Automated tests | 133 |

### 5.1.3 Contribution by member

| Member | Role | Commits | Primary areas |
|---|---|---|---|
| Suraj | AI/ML Engineer | 18 | LLM integration, RAG pipeline, prompt engineering, chat and quiz services, personalization transparency |
| Sandip Dey | Platform and Full-stack | 21 | Data model, migrations, knowledge graph, spaced repetition, onboarding, Docker, cloud deployment, dashboard and review interfaces |
| Udit Nayak | Backend API and QA | 20 | Authentication and security, repositories, routers and DTOs, the entire test suite, CI pipeline, auth and profile interfaces |

Every member contributed to both backend and frontend. The split is by concern
rather than by layer: each owns the interface that fronts their own backend
work, which kept the number of cross-member handoffs low.

### 5.1.4 Commit conventions

Conventional Commits throughout, with a scope where one applies:

```
feat(chat):     a new capability
fix(security):  a defect corrected
refactor(api):  behaviour-preserving restructuring
perf(graph):    a measured performance change
test:           test additions
docs(report):   documentation
ci:             pipeline changes
build:          build and packaging
chore:          scaffolding and maintenance
```

Message bodies state *why* rather than restating the diff. Commits fixing a
defect name the failure mode and, where relevant, why it went unnoticed — for
example, the commit correcting the hook-order violations records that the
ESLint rule was configured from the start but never run in CI.

### 5.1.5 Commit history screenshot

> **Figure 5.1 — Commit history.** Insert a screenshot of the repository's
> commit list showing the distribution across the development window.

> **Figure 5.2 — Contributor activity.** Insert the GitHub Insights →
> Contributors view showing all three members.

## 5.2 Weekly Progress Summary

| Week | Dates | Task Planned | Task Completed | Supervisor Remark |
|---|---|---|---|---|
| 1 | 14–19 Apr | Project scaffolding, database design, authentication | Docker Compose stack, Alembic setup, core configuration, 13-table schema, JWT authentication with bcrypt | |
| 2 | 20–26 Apr | LLM integration layer, reference search | Provider abstraction with Groq implementation, prompt builder, four-strategy response parser, SearXNG search provider | |
| 3 | 27 Apr – 3 May | Frontend foundation | Vite, React 19 and Tailwind scaffold; AuthContext, protected routes, login and signup with JWT storage | |
| 4 | 4–10 May | Knowledge graph and RAG data model | Concept node, edge and mastery models; learner profile; content embedding table with pgvector column | |
| 5 | 11–17 May | Retrieval pipeline and learning services | Local sentence-transformers embedder, indexer, cosine-similarity retriever; knowledge graph, onboarding and SM-2 services | |
| 6 | 18–24 May | Personalized tutoring and assessment | Chat service with profile-conditioned prompts and RAG grounding; quiz generation and grading; structured-output retry | |
| 7 | 25–31 May | Chat and onboarding interfaces | Chat page with session sidebar and markdown rendering; three-step onboarding with placement quiz | |
| 8 | 1–7 Jun | Dashboard and progress interfaces | Tiered concept grid with mastery bars and prerequisite locks; concept detail panel; recommendation card | |
| 9 | 8–14 Jun | Transparency, review queue, profile | "Why this response" indicator; spaced-repetition review page; profile editing; README; cloud configuration; first test suite and CI pipeline | |
| 10 | 15–21 Jun | Security review | Four broken-access-control defects identified and closed: session ownership on chat and quiz, message ownership on feedback, quiz answers withheld until submission | |
| 11 | 22–28 Jun | Correctness defects | Two React hook-order violations corrected; missing pgvector extension added to the initial migration; container entrypoint automating migration and seeding | |
| 12 | 29 Jun – 5 Jul | Documentation and performance | Setup instructions corrected and every environment variable documented; two N+1 query patterns eliminated; shared generation retry ladder extracted | |
| 13 | 6–12 Jul | API contract and unused features | Response models declared on all 24 endpoints; study streak derived from engagement history; progress analytics surfaced on the dashboard; authorization test suite | |
| 14 | 13–19 Jul | Frontend testing | Vitest and React Testing Library harness introduced; API client, quiz card, message bubble and data hooks covered; smoke test extended with cross-user probes | |
| 15 | 20–26 Jul | Pipeline and deployment configuration | Frontend lint, test and build added to CI; production image variant; Render blueprint; Vercel configuration with SPA rewrite | |
| 16 | 27 Jul – 2 Aug | Diagrams and runbook | Deployment runbook; architecture, component interaction, data flow, entity-relationship and sequence diagrams | |
| 17 | 3–9 Aug | Report chapters 1 to 5 | Front matter and abstract; introduction; implementation details and algorithms; testing and results; execution and deployment | |
| 18 | 10 Aug | Report completion | Conclusion and future work; references and appendices; report generator; screenshot capture guide | |

Weeks 1 to 9 were feature construction; weeks 10 to 18 were hardening,
verification and documentation. The transition is visible in the commit
history: the second phase contains no new user-facing capability apart from
surfacing two features that had been built but never wired to the interface.

## 5.3 Supervisor Interaction Summary

### 5.3.1 Review meetings

| # | Date | Topics Discussed | Key Feedback Received | Action Taken |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |

### 5.3.2 Summary of guidance

*To be completed with the supervisor's substantive feedback and how it
influenced the work.*

{{PAGEBREAK}}
