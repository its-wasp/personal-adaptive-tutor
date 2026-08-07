# CHAPTER 3: TESTING, VALIDATION AND RESULTS

## 3.1 Test Plan

### 3.1.1 Strategy

Testing is organised as a pyramid: many fast unit tests, a smaller layer of
component and endpoint tests, and one end-to-end suite against a running stack.

| Level | Count | Runtime | What it establishes |
|---|---|---|---|
| Backend unit | 81 | ~2 s | Algorithms, guards and parsing behave correctly in isolation |
| Frontend unit and component | 52 | ~2.5 s | Hooks and rendered components behave correctly |
| Endpoint | 6 | in the 81 | Request validation and auth rejection before any database access |
| End-to-end smoke | 30 assertions | ~60 s | Every endpoint works against a live stack, including cross-user isolation |
| Static and supply chain | 4 CI jobs | ~3 min | Lint, SAST, dependency CVEs, container CVEs |

**A deliberate constraint: no test database.** Every automated test runs
without PostgreSQL. Repositories are mocked at the boundary, so what is under
test is the decision a service makes, not the query that backs it. This keeps
the suite at roughly two seconds and makes CI trivial to configure, at the cost
of not exercising real SQL. The smoke test covers that gap against a real
database, and section 3.3.4 states the residual risk.

This is why the service layer raises domain exceptions such as `NotFoundError`
rather than `HTTPException`. It is what makes services testable without a web
framework.

### 3.1.2 What is tested, and what is not

**Covered by automated tests**

- Password hashing and JWT lifecycle, including expiry and tampering
- Session and message ownership guards on every entry point that accepts an id
- SM-2 interval progression, ease-factor floor, and scheduling side effects
- Study-streak calendar logic, including gaps, duplicates and boundaries
- LLM JSON extraction across all four recovery strategies
- The generation retry ladder, including the provider-rejection asymmetry
- Personalization reason derivation and its four-reason cap
- The API client: auth headers, error shapes, body parsing
- `useApiGet` and `useApiMutation`, including the stale-response guard
- `QuizCard` and `MessageBubble` rendering and interaction

**Not covered, and why**

- **Actual SQL.** No test database, per the constraint above.
- **Live LLM calls.** Non-deterministic, rate-limited and costly. Providers are
  faked with scripted outputs, which is what makes retry behaviour assertable at
  all.
- **Embedding quality.** Whether retrieved chunks are *relevant* is a
  judgement, not an assertion. Retrieval plumbing is tested; ranking quality is
  observed manually.
- **Most page components.** Seven route-level components have no tests. Stated
  as a limitation in 3.3.3 rather than glossed over.
- **Learning effectiveness.** Whether the system teaches better than a static
  course requires a controlled study with human participants, which is outside
  the scope of this submission.

### 3.1.3 Tools

| Tool | Level | Role |
|---|---|---|
| pytest | Backend unit | Runner, fixtures, parametrisation |
| pytest-cov | Backend | Statement coverage |
| unittest.mock | Backend | Repository and provider fakes |
| FastAPI TestClient | Endpoint | In-process requests, no server |
| Vitest | Frontend | Runner, jsdom environment |
| React Testing Library | Frontend | Behaviour-first component queries |
| requests | E2E | Drives the smoke suite |
| ruff | Static | Python linting |
| ESLint | Static | JavaScript linting, React hook rules |
| CodeQL | SAST | Security-focused static analysis |
| pip-audit | SCA | Python dependency CVEs |
| Trivy | SCA | Container image CVEs |

### 3.1.4 Continuous integration

Five jobs run on every push and pull request to `main`. `build-and-smoke` is
gated on the four before it.

```
quality-tests (backend)   ruff → pytest + coverage
frontend                  eslint → vitest + coverage → production build
sast                      CodeQL static analysis
sca                       pip-audit dependency scan
        ↓ all four must pass
build-and-smoke           docker build → Trivy scan → container /health probe
```

Trivy fails the build on any CRITICAL fixable vulnerability. pip-audit reports
without failing, since an unfixed upstream CVE should be visible without
blocking unrelated work.

## 3.2 Test Cases

Status recorded as of the final run. All 133 automated tests pass.

### 3.2.1 Authentication and security

| ID | Description | Input | Expected Output | Status |
|---|---|---|---|---|
| TC-01 | Password is hashed, not stored | `"s3cret-pass"` | Stored value differs from input, begins `$2` | Pass |
| TC-02 | Correct password verifies | Password + its hash | `True` | Pass |
| TC-03 | Wrong password rejected | Wrong password + hash | `False` | Pass |
| TC-04 | Hashing is salted | Same password twice | Two different hashes | Pass |
| TC-05 | JWT round-trips the user id | A UUID | Same UUID decoded | Pass |
| TC-06 | Malformed token rejected | `"not-a-real-token"` | `None` | Pass |
| TC-07 | Tampered token rejected | Valid token, last 3 chars altered | `None` | Pass |
| TC-08 | Expired token rejected | Token with `exp` one hour past | `None` | Pass |
| TC-09 | Token without subject rejected | Token lacking `sub` | `None` | Pass |
| TC-10 | Protected route needs a token | `GET /auth/me`, no header | HTTP 401 | Pass |
| TC-11 | Garbage bearer token rejected | `Authorization: Bearer nonsense` | HTTP 401 | Pass |

### 3.2.2 Request validation

| ID | Description | Input | Expected Output | Status |
|---|---|---|---|---|
| TC-12 | Empty signup body rejected | `POST /auth/signup {}` | HTTP 422 | Pass |
| TC-13 | Malformed email rejected | `email: "not-an-email"` | HTTP 422 | Pass |
| TC-14 | Health endpoint responds | `GET /health` | `{"status":"ok"}` | Pass |
| TC-15 | DB health degrades gracefully | `GET /health/db`, no database | HTTP 200 with error detail, no exception | Pass |

### 3.2.3 Access control

| ID | Description | Input | Expected Output | Status |
|---|---|---|---|---|
| TC-16 | Owner can load their session | Session owned by caller | Session returned | Pass |
| TC-17 | Missing session rejected | Unknown session id | `NotFoundError` | Pass |
| TC-18 | Another user's session rejected | Session owned by another user | `NotFoundError` | Pass |
| TC-19 | Missing and foreign are indistinguishable | Both cases | Identical error message | Pass |
| TC-20 | Reject before any write | Foreign session, `send_message` | Raises, `create_message` never called | Pass |
| TC-21 | Delete rejects foreign session | Foreign session id | Returns `False`, no delete issued | Pass |
| TC-22 | Quiz submission rejects foreign quiz | Quiz in another user's session | `NotFoundError`, no attempt recorded | Pass |
| TC-23 | Quiz generation rejects foreign session | Foreign session id | `NotFoundError` | Pass |
| TC-24 | E2E — read another user's conversation | Second account, first's session id | HTTP 404 | Pass |
| TC-25 | E2E — post into another user's session | Second account | HTTP 404 | Pass |
| TC-26 | E2E — delete another user's session | Second account | HTTP 404 | Pass |
| TC-27 | E2E — feedback on another user's message | Second account | HTTP 404 | Pass |
| TC-28 | Session list is per-user | Second account, `GET /chat/sessions` | Excludes first user's sessions | Pass |

### 3.2.4 Quiz answer confidentiality

| ID | Description | Input | Expected Output | Status |
|---|---|---|---|---|
| TC-29 | Generation withholds the answer | `POST /quiz/generate` | Response has no `correct_option` | Pass |
| TC-30 | Generation withholds the explanation | `POST /quiz/generate` | Response has no `explanation` | Pass |
| TC-31 | Unanswered quiz withholds the answer | `GET /conversation`, no attempt | `correct_option` is null | Pass |
| TC-32 | Unanswered quiz remains answerable | `GET /conversation` | `quiz_id` present | Pass |
| TC-33 | Answer revealed after submission | `POST /quiz/submit` | `correct_option` and explanation returned | Pass |
| TC-34 | UI hides the answer pre-submission | Unanswered `quizData` | No hint, explanation or result rendered | Pass |

### 3.2.5 Spaced repetition

| ID | Description | Input | Expected Output | Status |
|---|---|---|---|---|
| TC-35 | First success moves 1 → 6 days | interval 1, correct | interval 6.0 | Pass |
| TC-36 | Later success multiplies by ease | interval 6, EF 2.5, correct | interval 15.0 | Pass |
| TC-37 | Failure resets the interval | interval 42, incorrect | interval 1.0 | Pass |
| TC-38 | Ease factor never breaches its floor | EF 1.3, five failures | EF ≥ 1.3 | Pass |
| TC-39 | Strong recall raises the ease factor | mastery 0.9, correct | EF > 2.5 | Pass |
| TC-40 | Next review follows last review | Any review | `next_review_at` > `last_reviewed_at` | Pass |
| TC-41 | Schedule change is committed | Any review | `commit()` called once | Pass |

### 3.2.6 Study streak

| ID | Description | Input | Expected Output | Status |
|---|---|---|---|---|
| TC-42 | No activity | `[]` | 0 | Pass |
| TC-43 | Consecutive run | 4 consecutive days | 4 | Pass |
| TC-44 | Gap terminates the run | today, −1, −3, −4 | 2 | Pass |
| TC-45 | Unordered input handled | Shuffled dates | Correct length | Pass |
| TC-46 | Duplicates collapse | Today three times, plus yesterday | 2 | Pass |
| TC-47 | Yesterday still counts as live | −1, −2, −3 | 3 | Pass |
| TC-48 | Two days idle breaks the streak | −2, −3, −4 | 0 | Pass |

### 3.2.7 LLM output parsing

| ID | Description | Input | Expected Output | Status |
|---|---|---|---|---|
| TC-49 | Clean JSON parsed | `{"a": 1}` | Parsed dictionary | Pass |
| TC-50 | Fenced JSON recovered | ```` ```json … ``` ```` with prose | Parsed dictionary | Pass |
| TC-51 | JSON amid prose recovered | `Sure! {...} that is it.` | Parsed dictionary | Pass |
| TC-52 | Unescaped newlines recovered | Literal newline in a string value | Both fields recovered | Pass |
| TC-53 | Unrecoverable input raises | `"there is no json here"` | `ValueError` | Pass |
| TC-54 | Empty required field rejected | `{"title":"T","explanation":""}` | `ValueError` | Pass |
| TC-55 | Too few quiz options rejected | One option | `ValueError` | Pass |
| TC-56 | Missing correct option rejected | No `correct_option` | `ValueError` | Pass |

### 3.2.8 Generation retry ladder

| ID | Description | Input | Expected Output | Status |
|---|---|---|---|---|
| TC-57 | Valid first attempt short-circuits | Good JSON | One provider call | Pass |
| TC-58 | JSON mode requested | Any call | `json_mode=True` | Pass |
| TC-59 | Malformed output triggers one retry | Bad, then good | Two calls, parsed result | Pass |
| TC-60 | Retry runs cooler | Bad, then good | Second temperature < first | Pass |
| TC-61 | Retry replays output and correction | Bad, then good | Messages are user, assistant, user | Pass |
| TC-62 | Provider rejection has nothing to replay | `ValueError`, then good | Messages are user, user | Pass |
| TC-63 | Contract violation counts as malformed | Empty field, then good | Two calls | Pass |
| TC-64 | Double failure raises a clean error | Bad, bad | `ValueError` with friendly message | Pass |
| TC-65 | Original error is chained | Bad, bad | `__cause__` set | Pass |
| TC-66 | Never more than two attempts | Bad, bad | Exactly two calls | Pass |

### 3.2.9 Personalization signals

| ID | Description | Input | Expected Output | Status |
|---|---|---|---|---|
| TC-67 | No profile yields no reasons | `None` | `[]` | Pass |
| TC-68 | Learning style produces a reason | `EXAMPLE_FIRST` | "Example-first" present | Pass |
| TC-69 | Weaknesses and strengths both surface | Both set | "Extra care", "Built on strengths" | Pass |
| TC-70 | Memory produces a reason | `learner_summary` set | "Remembered you" | Pass |
| TC-71 | Retrieval count pluralises | 2 chunks | "2 reference explanations" | Pass |
| TC-72 | Singular wording for one chunk | 1 chunk | "1 reference explanation." | Pass |
| TC-73 | Capped at four reasons | Six signals set | Exactly 4 returned | Pass |

### 3.2.10 Frontend — API client and hooks

| ID | Description | Input | Expected Output | Status |
|---|---|---|---|---|
| TC-74 | Bearer token attached | Token stored | `Authorization: Bearer …` | Pass |
| TC-75 | No header without a token | Store empty | Header absent | Pass |
| TC-76 | `auth: false` suppresses the header | Login request | Header absent | Pass |
| TC-77 | Error detail surfaced | HTTP 404 with detail | `ApiError` carries status and detail | Pass |
| TC-78 | Non-JSON error body handled | `"Bad Gateway"` text | `ApiError` with status 502 | Pass |
| TC-79 | Empty body yields null | Empty response | `null` | Pass |
| TC-80 | Fetch on mount | `useApiGet(path)` | Data populated, loading false | Pass |
| TC-81 | `skip` suppresses the request | `{skip: true}` | No call issued | Pass |
| TC-82 | Path change refetches | Path changes | Second call with the new path | Pass |
| TC-83 | Stale response discarded | Slow response for a replaced path | Late payload ignored | Pass |
| TC-84 | Mutation rethrows and records | Rejecting request | Throws; `error` set; `loading` false | Pass |

### 3.2.11 Frontend — components

| ID | Description | Input | Expected Output | Status |
|---|---|---|---|---|
| TC-85 | Quiz renders question and options | Unanswered quiz | Question plus four options shown | Pass |
| TC-86 | Submit gated on a selection | No option chosen | Submit disabled | Pass |
| TC-87 | Submission payload correct | Option B chosen | Posts `{quiz_id, selected_option:"B"}` | Pass |
| TC-88 | Correct answer reported | `correct: true` | "Correct!", points, explanation | Pass |
| TC-89 | Hint shown only when wrong | `correct: false` | Hint rendered | Pass |
| TC-90 | Answered quiz restores state | Prior attempt present | Completed state, no submit button | Pass |
| TC-91 | Failed submission stays answerable | Request rejects | Submit re-enabled | Pass |
| TC-92 | Markdown rendered for assistant | `**bold idea**` | `<strong>` element | Pass |
| TC-93 | Quiz message swaps in the card | `message_type: QUIZ` | Card shown, placeholder text absent | Pass |
| TC-94 | Reason pill starts collapsed | Two reasons | Count shown, details hidden | Pass |
| TC-95 | Reason pill expands | Click | All reasons and details shown | Pass |
| TC-96 | No pill on learner messages | User message with reasons | Pill absent | Pass |

### 3.2.12 End-to-end smoke

| ID | Description | Input | Expected Output | Status |
|---|---|---|---|---|
| TC-97 | Health and DB connectivity | Running stack | Both report ok | Pass |
| TC-98 | Signup and login | New credentials | Token issued both times | Pass |
| TC-99 | Onboarding completes | Preferences plus 10 answers | Level assigned, mastery seeded | Pass |
| TC-100 | Graph loads with mastery | `GET /graph/dsa` | 25 nodes, 37 edges, mastery overlay | Pass |
| TC-101 | Recommendation returned | `GET /graph/dsa/recommend` | An unlocked, unmastered concept | Pass |
| TC-102 | Session creation generates a lesson | Topic "Arrays" | Session with title and opening explanation | Pass |
| TC-103 | Message round-trip | A question | Personalized reply returned | Pass |
| TC-104 | Quiz generation and grading | Generate then submit | Result with explanation | Pass |
| TC-105 | Review queue responds | `GET /review/due` | Queue plus statistics | Pass |
| TC-106 | Analytics respond | `GET /analytics/me` | Points, accuracy, per-topic breakdown | Pass |
| TC-107 | Session deletion (CRUD delete) | `DELETE /chat/{id}` | `{"deleted": true}` | Pass |
| TC-108 | Second delete is idempotent-safe | Same id again | HTTP 404 | Pass |

## 3.3 Results and Analysis

### 3.3.1 Test execution

| Suite | Tests | Passed | Failed | Runtime |
|---|---|---|---|---|
| Backend (pytest) | 81 | 81 | 0 | 2.11 s |
| Frontend (Vitest) | 52 | 52 | 0 | 2.52 s |
| **Total** | **133** | **133** | **0** | **~4.6 s** |

The suite grew from 44 tests to 133 during the hardening phase — 37 backend
tests accompanying the security and correctness work, and 52 frontend tests
where previously no frontend test tooling existed at all.

### 3.3.2 Coverage

**Backend — 60% of 2,034 statements.** Distribution is uneven by design:

| Module | Coverage | Comment |
|---|---|---|
| `utils/security.py` | 100% | Authentication primitives, fully exercised |
| `llm/structured.py` | 100% | Retry ladder, all branches |
| `models/*` | 100% | Declarative; imported and validated |
| `llm/personalization_reasons.py` | 97% | Reason derivation |
| `llm/response_parser.py` | 94% | All four recovery strategies |
| `services/quiz_service.py` | 61% | Guards covered; LLM path not |
| `services/spaced_repetition_service.py` | 60% | SM-2 covered; queue reads not |
| `services/chat_service.py` | 37% | Guards covered; orchestration needs a database |
| `llm/prompt_builder.py` | 7% | Produces prompt text; asserted indirectly |
| `rag/content_seeder.py` | 0% | One-off operational script |

The pattern is consistent: logic that can be decided in isolation is at or near
full coverage, while code whose behaviour is "call the database, then call the
model" is left to the smoke test. That is the intended consequence of testing
without a database, not an oversight.

**Frontend — 13.7% of statements, 80.15% of branches.** The gap between those
two numbers is the honest headline. The four modules under test are complete:

| Module | Statements | Branches |
|---|---|---|
| `lib/api.js` | 100% | 95% |
| `hooks/useApi.js` | 100% | 96% |
| `components/chat/QuizCard.jsx` | 100% | 93% |
| `components/chat/MessageBubble.jsx` | 100% | 95% |

Everything else is at zero: seven page components, the auth context, and six
further components. Section 3.3.3 treats this as the principal limitation.

### 3.3.3 Defects found and resolved

Testing and review during the hardening phase surfaced eleven defects. Four
were security issues of the same class.

| # | Defect | Severity | Detected by | Resolution |
|---|---|---|---|---|
| D1 | `send_message` and `get_conversation` never checked session ownership | Critical | Code review | Shared `_assert_owns_session` guard |
| D2 | `/quiz/generate` and `/quiz/submit` never checked ownership | Critical | Code review | `_owned_session`, filtered in SQL |
| D3 | `/feedback` accepted any `message_id` | High | Code review | Ownership resolved through the session |
| D4 | Quiz answers served before submission | High | Code review | Withheld until an attempt exists |
| D5 | `Chat.jsx` returned before later hooks | High | ESLint | Gate moved below all hooks |
| D6 | `Onboarding.jsx` had the same fault | High | ESLint | Same fix |
| D7 | No `CREATE EXTENSION vector`; fresh clone could not migrate | High | Fresh-clone attempt | Added to the initial migration |
| D8 | Conversation payload omitted `quiz_id` | Medium | Writing TC-32 | Included in the payload |
| D9 | N+1 on personalization context | Medium | Code review | Batched into one query |
| D10 | N+1 on prerequisite resolution | Medium | Code review | Single edge query |
| D11 | `streak_days` never written | Low | Code review | Derived from engagement events |

**Analysis of D1–D4.** All four are broken access control — OWASP Top 10
A01:2021 [3]. Each endpoint authenticated correctly and then failed to
authorise: it confirmed *who* the caller was and never checked *whether that
caller owned the object they had named*. That is the defining shape of an
insecure direct object reference.

The pattern is instructive. `delete_session` had the ownership check from the
beginning, because deletion obviously feels dangerous. Reading a conversation
does not feel dangerous, so the same check was never written — even though the
information disclosure is arguably worse than the deletion.

Two properties were adopted in response, both asserted by tests:

1. **404, never 403.** Answering 403 for "exists but not yours" confirms the id
   is real and turns the endpoint into an oracle for enumerating other learners'
   sessions. TC-19 asserts the two error messages are byte-identical.
2. **Authorise before writing.** `send_message` previously inserted the
   learner's message and *then* looked up the session, so an unknown id left an
   orphan row. TC-20 asserts nothing is written on the rejection path.

**Analysis of D5 and D6.** `eslint-plugin-react-hooks` was configured from the
first frontend commit and would have caught both immediately. The CI pipeline
never ran frontend lint. The defect was not the missing rule but the missing
gate, which is why the fix was to add the CI job, not merely to correct the two
files.

**Analysis of D7.** Found by doing what an examiner would do: cloning the
repository and following the README. Migration failed on the `Vector(384)`
column because nothing had ever enabled the extension. It had gone unnoticed
because every existing development database had been created before that
migration split, or had the extension enabled by hand. The fix was accompanied
by an entrypoint that migrates and seeds automatically, so the documented path
and the working path are now the same path.

### 3.3.4 Security scanning

| Scanner | Scope | Result |
|---|---|---|
| CodeQL | Python source | No alerts |
| pip-audit | Backend dependencies | Reported; non-blocking by policy |
| Trivy | Container image | No CRITICAL fixable findings; build fails if any appear |
| ESLint | JavaScript | 0 errors, 1 warning |
| ruff | Python | 0 findings across `app`, `tests`, `scripts` |

Worth noting that CodeQL did **not** find D1–D4. Broken access control is a
statement about intended authorisation policy, and static analysis has no way
to know that a `chat_session_id` from a request body ought to be checked against
the authenticated user. Finding that class of defect required reading the code
with the question "who is allowed to do this?" in mind. The tests written
afterwards make the answer permanent.

### 3.3.5 Performance observations

Measured locally against Docker Compose; indicative rather than benchmarked.

| Operation | Observed | Note |
|---|---|---|
| `GET /health` | < 10 ms | No database access |
| `GET /graph/dsa` | ~40 ms | 25 nodes, 37 edges, mastery overlay |
| `GET /profile/me` | ~25 ms | Down from ~180 ms before D9 was fixed |
| `POST /chat/message` | 2–6 s | Dominated by LLM latency |
| `POST /quiz/generate` | 1–3 s | Dominated by LLM latency |
| Embedding a query | ~15 ms | Local `all-MiniLM-L6-v2` |
| Vector search | < 20 ms | Cosine distance over a few hundred rows |
| First cloud request | 30–60 s | Free-tier cold start |

The two N+1 fixes were the only measurable wins available. Everything else is
LLM latency, which cannot be optimised from this side of the API — only hidden,
by streaming responses, which section 6.4 identifies as future work.

### 3.3.6 Limitations of this validation

Stated plainly:

1. **No database in the automated suite.** Query correctness, constraint
   enforcement and migration behaviour are exercised only by the smoke test,
   which is run manually. A misspelled column in a rarely-taken branch would
   reach production.
2. **Frontend page components are untested.** 13.7% statement coverage. The
   seven route components contain real logic — the scroll-anchoring in
   `Chat.jsx`, the tier grouping in `ConceptGrid.jsx` — and none of it is
   asserted.
3. **LLM behaviour is faked throughout.** Tests prove the system handles good
   and bad model output correctly. They say nothing about whether the tutor's
   explanations are any *good*.
4. **No load testing.** Correctness under concurrency is unmeasured. The
   `get_or_create_profile` pattern would race under simultaneous requests for a
   new user.
5. **No accessibility audit.** Semantic elements and ARIA labels were used
   throughout, but no screen-reader or contrast testing was performed.

{{PAGEBREAK}}
