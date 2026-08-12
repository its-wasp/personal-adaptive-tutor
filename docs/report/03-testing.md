# CHAPTER 3: TESTING, VALIDATION AND RESULTS

## 3.1 Test Plan

### 3.1.1 Strategy

Testing is arranged as a pyramid: a lot of fast unit tests, fewer component and
endpoint tests, and one end-to-end suite run against a live stack.

| Level | Count | Runtime | What it checks |
|---|---|---|---|
| Backend unit | 95 | ~2 s | Algorithms, guards and parsing in isolation |
| Frontend unit and component | 52 | ~2.5 s | Hooks and rendered components |
| End-to-end smoke | 40 assertions | ~60 s | Every endpoint against a running system |
| Static and supply chain | 4 CI jobs | ~3 min | Lint, SAST, dependency and container CVEs |

One decision shaped everything else: **no test database.** All automated tests
run without PostgreSQL, with repositories mocked at the boundary. What is being
tested is the decision a service makes, not the query behind it. This keeps the
suite at about two seconds and makes CI trivial to set up, but it means real SQL
is never exercised. The smoke test covers that against a live database, and
section 3.3.5 says what risk remains.

This is also why services raise their own exceptions rather than
`HTTPException`. It is what lets them be tested without a web framework.

### 3.1.2 What is and is not covered

Covered: password hashing and the JWT lifecycle, ownership guards on every
endpoint that takes an ID, SM-2 interval maths, streak calendar logic, all four
JSON recovery strategies, the generation retry ladder, personalization reason
derivation, the API client, both data hooks, and the quiz and message
components.

Not covered, with reasons:

- **Real SQL**, because there is no test database.
- **Live LLM calls.** They are non-deterministic and rate-limited. Providers are
  faked with scripted responses, which is what makes the retry behaviour
  testable at all.
- **Retrieval quality.** Whether the chunks that come back are *relevant* is a
  judgement, not an assertion. We tested the plumbing and checked the ranking by
  hand.
- **Most page components.** Seven route components have no tests. This is listed
  as a limitation in 3.3.5 rather than glossed over.
- **Learning effectiveness**, which would need a study with real students.

### 3.1.3 Tools

pytest with pytest-cov and `unittest.mock` for the backend, FastAPI's TestClient
for endpoint tests, Vitest with React Testing Library for the frontend, and
`requests` for the smoke suite. Static checks use ruff, ESLint, CodeQL for
security analysis, pip-audit for dependency CVEs and Trivy for the container
image.

### 3.1.4 Continuous integration

Five jobs run on every push and pull request. The build job waits for the other
four.

```
quality-tests (backend)   ruff → pytest + coverage
frontend                  eslint → vitest + coverage → build
sast                      CodeQL
sca                       pip-audit
        ↓ all four must pass
build-and-smoke           docker build → Trivy scan → /health probe
```

Trivy fails the build on any fixable CRITICAL vulnerability. pip-audit reports
without failing, since an unfixed upstream CVE should be visible but should not
block unrelated work.

## 3.2 Test Cases

A representative selection. All 147 automated tests pass.

| ID | Description | Input | Expected Output | Status |
|---|---|---|---|---|
| TC-01 | Password is hashed, not stored | `"s3cret-pass"` | Stored value differs, starts `$2` | Pass |
| TC-02 | Wrong password rejected | Wrong password + hash | `False` | Pass |
| TC-03 | Hashing is salted | Same password twice | Two different hashes | Pass |
| TC-04 | JWT round-trips the user id | A UUID | Same UUID decoded | Pass |
| TC-05 | Tampered token rejected | Token with last 3 chars altered | `None` | Pass |
| TC-06 | Expired token rejected | `exp` one hour in the past | `None` | Pass |
| TC-07 | Protected route needs a token | `GET /auth/me`, no header | HTTP 401 | Pass |
| TC-08 | Invalid email rejected | `email: "not-an-email"` | HTTP 422 | Pass |
| TC-09 | DB health degrades gracefully | `/health/db`, no database | HTTP 200 with error detail | Pass |
| TC-10 | Owner can load their session | Session owned by caller | Session returned | Pass |
| TC-11 | Another user's session rejected | Session owned by someone else | `NotFoundError` | Pass |
| TC-12 | Missing and foreign look identical | Both cases | Same error message | Pass |
| TC-13 | Reject before any write | Foreign session, `send_message` | Raises, nothing inserted | Pass |
| TC-14 | Quiz submission rejects foreign quiz | Quiz in another user's session | `NotFoundError`, no attempt saved | Pass |
| TC-15 | Generation withholds the answer | `POST /quiz/generate` | No `correct_option` or `explanation` | Pass |
| TC-16 | Unanswered quiz withholds the answer | `GET /conversation`, no attempt | `correct_option` is null | Pass |
| TC-17 | Unanswered quiz stays answerable | `GET /conversation` | `quiz_id` present | Pass |
| TC-18 | Answer revealed after submission | `POST /quiz/submit` | Answer and explanation returned | Pass |
| TC-19 | First success moves 1 → 6 days | Interval 1, correct | Interval 6.0 | Pass |
| TC-20 | Later success multiplies by ease | Interval 6, EF 2.5, correct | Interval 15.0 | Pass |
| TC-21 | Failure resets the interval | Interval 42, incorrect | Interval 1.0 | Pass |
| TC-22 | Ease factor holds at its floor | EF 1.3, five failures | EF ≥ 1.3 | Pass |
| TC-23 | Gap ends the streak | Active today, −1, −3, −4 | 2 | Pass |
| TC-24 | Yesterday still counts | Active −1, −2, −3 | 3 | Pass |
| TC-25 | Fenced JSON recovered | ```` ```json … ``` ```` with prose | Parsed dictionary | Pass |
| TC-26 | Unescaped newlines recovered | Literal newline in a string value | Both fields recovered | Pass |
| TC-26a | Escape sequences decoded, not passed through | Raw newline beside escaped ones | No literal backslash-n in output | Pass |
| TC-26b | Code fences survive recovery | Explanation containing a python fence | Fence markers intact | Pass |
| TC-27 | Empty required field rejected | `{"title":"T","explanation":""}` | `ValueError` | Pass |
| TC-28 | Malformed output triggers one retry | Bad, then good | Two calls, parsed result | Pass |
| TC-29 | Provider rejection has nothing to replay | `ValueError`, then good | Retry has no assistant turn | Pass |
| TC-30 | Never more than two attempts | Bad, bad | Exactly two calls, clean error | Pass |
| TC-31 | Reasons capped at four | Six signals set | Exactly 4 returned | Pass |
| TC-32 | Bearer token attached | Token stored | `Authorization: Bearer …` | Pass |
| TC-33 | Error detail surfaced | HTTP 404 with detail | `ApiError` carries status and detail | Pass |
| TC-34 | Stale response discarded | Slow response for a replaced path | Late payload ignored | Pass |
| TC-35 | Submit gated on a selection | No option chosen | Submit disabled | Pass |
| TC-36 | Quiz reports a correct answer | `correct: true` | "Correct!", points, explanation | Pass |
| TC-37 | Answered quiz restores state | Prior attempt present | Completed state, no submit button | Pass |
| TC-38 | Reason pill starts collapsed | Two reasons | Count shown, details hidden | Pass |
| TC-39 | No pill on learner messages | User message with reasons | Pill absent | Pass |
| TC-40 | E2E: read another user's conversation | Second account | HTTP 404 | Pass |
| TC-41 | E2E: post into another user's session | Second account | HTTP 404 | Pass |
| TC-42 | E2E: feedback on another user's message | Second account | HTTP 404 | Pass |
| TC-43 | E2E: session list is per-user | Second account | Excludes first user's sessions | Pass |
| TC-44 | E2E: onboarding completes | Preferences plus 10 answers | Level assigned, mastery seeded | Pass |
| TC-45 | E2E: graph loads with mastery | `GET /graph/dsa` | 25 nodes, 37 edges, mastery overlay | Pass |
| TC-46 | E2E: session generates a lesson | Topic "Arrays" | Session with title and explanation | Pass |
| TC-47 | E2E: quiz generated and graded | Generate then submit | Result with explanation | Pass |
| TC-48 | E2E: session deletion | `DELETE /chat/{id}` | `{"deleted": true}` | Pass |
| TC-49 | E2E: second delete returns 404 | Same id again | HTTP 404 | Pass |

## 3.3 Results and Analysis

### 3.3.1 Execution

| Suite | Tests | Passed | Failed | Runtime |
|---|---|---|---|---|
| Backend (pytest) | 95 | 95 | 0 | 2.25 s |
| Frontend (Vitest) | 52 | 52 | 0 | 2.52 s |
| **Total** | **147** | **147** | **0** | **~4.8 s** |

The suite grew from 44 tests to 147 during the hardening phase. The frontend had
no test tooling at all before that.

The smoke test was run against the live stack on a fresh database: 40
assertions, no failures, 61.5 seconds including real LLM calls.

### 3.3.2 Coverage

Backend statement coverage is 60% of 2,034 statements, distributed unevenly on
purpose:

| Module | Coverage |
|---|---|
| `utils/security.py` | 100% |
| `llm/structured.py` | 100% |
| `models/*` | 100% |
| `llm/response_parser.py` | 94% |
| `services/quiz_service.py` | 61% |
| `services/chat_service.py` | 37% |
| `rag/content_seeder.py` | 0% |

The pattern follows from the no-database decision. Logic that can be decided in
isolation is near full coverage; code whose job is "call the database, then call
the model" is left to the smoke test.

Frontend coverage is 13.7% of statements but 80% of branches. The four modules
under test are complete (`api.js`, `useApi.js`, `QuizCard`, `MessageBubble`, all
at 100% statements). Thirteen other files, including all seven page components,
are at zero. That gap is the main weakness in our testing and is listed in
3.3.5.

### 3.3.3 Defects found and fixed

Thirteen defects were found during the hardening phase. Four were the same class
of security bug.

| # | Defect | Severity | Found by | Fix |
|---|---|---|---|---|
| D1 | `send_message` and `get_conversation` never checked session ownership | Critical | Code review | Shared ownership guard |
| D2 | Quiz generate and submit never checked ownership | Critical | Code review | Ownership filtered in SQL |
| D3 | Feedback accepted any `message_id` | High | Code review | Ownership resolved via the session |
| D4 | Quiz answers served before submission | High | Code review | Withheld until an attempt exists |
| D5 | `Chat.jsx` returned before later hooks | High | ESLint | Gate moved below all hooks |
| D6 | Same fault in `Onboarding.jsx` | High | ESLint | Same fix |
| D7 | No `CREATE EXTENSION vector`, so a fresh clone could not migrate | High | Fresh-clone attempt | Added to the initial migration |
| D8 | Conversation payload omitted `quiz_id` | Medium | Writing TC-17 | Added to the payload |
| D9 | N+1 query building the personalization context | Medium | Code review | Batched into one query |
| D10 | N+1 query resolving prerequisites | Medium | Code review | Single edge query |
| D11 | `streak_days` never written | Low | Code review | Derived from engagement events |
| D12 | Malformed-JSON recovery returned escape sequences verbatim, so opening explanations rendered as one unbroken line | Medium | Manual use after the model change | Repair the input and parse it, instead of rebuilding the object by hand |
| D13 | Only one explanation in three survived the JSON validator, so most requests hit the retry, which over-escaped the newlines | High | Sampling generation after D12 recurred | Explanations moved to a delimited format needing no escaping; quizzes stay on JSON |

**D1 to D4** are all broken access control, which is A01 in the OWASP Top 10
[3]. Each endpoint authenticated correctly and then failed to authorise. It
checked *who* the caller was and never checked whether that caller owned the
thing they had named.

What we found interesting is that `delete_session` had the ownership check from
the start, because deleting obviously feels dangerous. Reading a conversation
does not feel dangerous, so nobody wrote the same check, even though leaking
somebody's private tutoring history is arguably worse than deleting a session.

Two rules came out of it, both now asserted by tests. First, answer 404 and
never 403: a 403 confirms the ID is real and turns the endpoint into a way of
discovering other people's session IDs. Second, authorise before writing.
`send_message` used to insert the learner's message and *then* look up the
session, so an unknown ID left an orphan row behind.

**D5 and D6** were both caught by ESLint, which had the React hooks plugin
enabled from the very first frontend commit. CI never ran frontend lint, so
nobody saw the errors. The real fix was adding the CI job, not just correcting
the two files.

**D7** was found by doing what an examiner would do: cloning the repository and
following the README. The migration failed because nothing had ever enabled the
pgvector extension. It had gone unnoticed because every development database
already had it enabled by hand. We fixed it and added a container entrypoint
that migrates and seeds on start, so the documented path and the working path
are now the same.

### 3.3.4 Security scanning

| Scanner | Scope | Result |
|---|---|---|
| CodeQL | Python source | No alerts |
| pip-audit | Dependencies | Reported, non-blocking |
| Trivy | Container image | No fixable CRITICAL findings |
| ESLint | JavaScript | 0 errors |
| ruff | Python | 0 findings |

Worth noting that CodeQL did not find D1 to D4. Broken access control is a
statement about what the authorisation policy is supposed to be, and a static
analyser has no way to know that a session ID from a request body ought to be
checked against the logged-in user. Finding those needed someone reading the
code and asking who is allowed to do this.

### 3.3.5 Limitations of this validation

1. **No database in the automated tests.** Query correctness and constraints are
   only exercised by the smoke test, which is run by hand.
2. **Page components are untested**, 13.7% frontend coverage. The scroll
   anchoring in `Chat.jsx` and the tier grouping in `ConceptGrid.jsx` contain
   real logic that nothing asserts.
3. **LLM behaviour is faked.** The tests show the system handles good and bad
   model output. They say nothing about whether the explanations are any good.
4. **No load testing.** `get_or_create_profile` would race if two requests
   arrived at once for a new user.
5. **No accessibility audit.** We used semantic elements and ARIA labels but did
   not test with a screen reader.

{{PAGEBREAK}}
