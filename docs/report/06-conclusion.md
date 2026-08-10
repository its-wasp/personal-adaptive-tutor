# CHAPTER 6: CONCLUSION AND FUTURE WORK

## 6.1 Summary of Implementation

This project delivered a working adaptive tutoring platform for Data Structures
and Algorithms: a React single-page application over a FastAPI backend, a
PostgreSQL database with vector search, and a hosted language model.

The system comprises roughly 9,900 lines across 130 source files — 24 REST
endpoints, 13 database tables, 3 migrations, 25 concepts with 37 typed
prerequisite edges, and 133 automated tests behind a five-stage CI pipeline.

The substance of the work is not the chat interface but the four mechanisms
behind it. An explicit learner profile is translated into imperative
instructions in every system prompt. A natural-language memory is revised by the
model every five messages and carried forward across sessions. Retrieved
reference material grounds generation through vector similarity search. A
prerequisite graph tracks per-concept mastery, which in turn gates progression,
targets questions and drives an SM-2 revision schedule. Each is a durable
property of the system rather than an instruction appended to a prompt.

## 6.2 Achievements Against Objectives

| # | Objective | Outcome |
|---|---|---|
| O1 | Model the learner explicitly | **Met.** Preferences persisted across five dimensions; mastery derived from performance via a blended estimator, not self-report |
| O2 | Condition responses on that model | **Met.** Modular prompt assembly injects profile, memory and retrieved material on every generation |
| O3 | Give the tutor durable memory | **Met.** Summary revised every five messages, merged rather than replaced, carried across sessions and surfaced in the profile page |
| O4 | Ground generation in reference material | **Met locally, degraded in production.** Full pipeline works with the local embedding model; the free-tier deployment omits it and falls back cleanly. See 6.3 |
| O5 | Represent the subject as a prerequisite graph | **Met.** 25 concepts, 37 typed edges, 5 tiers, unlocking at 0.6 mastery, lowest-mastery-first recommendation |
| O6 | Schedule revision on evidence | **Met.** SM-2 with correct ease-factor arithmetic and floor, driven by quiz outcomes, surfaced as a review queue |
| O7 | Make the adaptation visible | **Met.** Signals snapshotted at generation time and shown per message. Snapshotting rather than recomputing means an old message reflects the profile that actually shaped it |
| O8 | Engineer it as a deployable system | **Met.** Layered architecture, migrations, 133 tests, CI with SAST and dependency and container scanning, declarative cloud configuration |

Beyond the stated objectives, a security review during the hardening phase
identified and closed four broken-access-control defects that would have
allowed any authenticated learner to read and modify another's data. That work
is documented in section 3.3.3.

## 6.3 Limitations

Stated plainly, since each bounds what the system can currently claim.

**RAG is unavailable in the deployed instance.** The embedding model requires
PyTorch, which pushes the image beyond the free tier's size limit. The
architecture handles this cleanly — the tutor degrades to profile-driven
personalization without error — but the deployed system demonstrates three of
the four personalization mechanisms rather than all four. Paid hosting, or
switching to a hosted embedding API, resolves it.

**Effectiveness is unmeasured.** The system is demonstrably *adaptive*: it can
be shown to produce different explanations of the same concept for different
profiles. Whether that adaptation improves learning outcomes is unestablished.
Answering it requires a controlled study with human participants over weeks,
which is beyond a single-semester submission.

**Mastery rests on multiple-choice evidence.** A learner can select the right
option by elimination without understanding, and a four-option question samples
a concept narrowly. Mastery is therefore a noisier signal than the numeric score
suggests. The confidence field records evidence volume, but nothing currently
consumes it.

**A single subject.** The schema is subject-agnostic — `concept_nodes` carries a
`subject` column and every query filters on it — but only the DSA graph is
authored. The claim that adding another subject is a data exercise is
architecturally sound but untested.

**Test coverage is uneven.** Backend statement coverage is 60%; frontend is
13.7%, with seven route-level components untested. No automated test touches a
real database, so query correctness and constraint enforcement rest on a
manually-run smoke suite.

**No concurrency handling.** `get_or_create_profile` and similar
read-then-create patterns would race under simultaneous requests for the same
new user. Single-user usage never exercises this; a class of thirty starting
at once might.

**Cost and rate limits shape behaviour.** Retrieval is capped at two or three
chunks and reference text truncated to 500 characters, to stay inside the
context budget and the free tier. A larger budget would allow richer grounding.

## 6.4 Future Enhancements

Ordered by the ratio of value to effort, given the existing architecture.

**Stream responses.** Chat replies take two to six seconds, essentially all of
it model latency, and the interface shows a static "Tutor is thinking…" for the
duration. Groq supports server-sent events; FastAPI supports
`StreamingResponse`. Perceived latency would drop to a few hundred
milliseconds. This is the single largest available improvement to the
experience and requires no architectural change.

**Free-text answers with rubric grading.** The strongest evidence of
understanding is an explanation in the learner's own words. Asking the learner
to explain a concept and grading it against a model-generated rubric would give
a far better mastery signal than multiple choice — at the cost of a
reliability problem worth studying in its own right.

**Consume the confidence signal.** `concept_mastery.confidence` is computed and
stored and nothing reads it. A mastery of 0.8 from two answers should not gate
progression as strongly as 0.8 from twenty. Weighting unlock decisions by
confidence is a small change to one predicate with a real effect on pacing.

**Author a second subject.** The most direct test of the generality claim.
Operating Systems or Databases would exercise the graph model against a
differently-shaped prerequisite structure and reveal any DSA-specific
assumptions.

**Adaptive question difficulty.** Quizzes currently take difficulty from the
session level. Selecting difficulty per question from current mastery — item
response theory in its simplest form — would keep the learner nearer the edge of
their competence, which is where the learning is.

**Learner-facing analytics.** Engagement events are recorded on every
interaction and only the streak is derived from them. Time-of-day patterns,
session-length trends and per-concept time investment are all already in the
table, unqueried.

**Code execution.** A sandboxed judge would let the tutor set implementation
exercises rather than only conceptual questions. Substantial work — process
isolation, resource limits, multi-language support — but it is the natural
completion of a DSA tutor.

**A test database in CI.** A disposable PostgreSQL service container would let
repository tests run against real SQL and close the largest gap in the current
validation strategy, at the cost of a slower pipeline.

## 6.5 Concluding Remarks

Bloom's 2 Sigma finding framed one-to-one tutoring as a target rather than a
curiosity: the challenge is to find scalable methods that approach its results.
Language models make the generation half of that problem tractable almost
trivially. This project's contention is that generation is not the hard part.

The hard part is everything that makes a tutor's advice *personal*: maintaining
a model of the learner that survives across sessions, deciding what to teach
next from what they demonstrably know, grounding explanations so they stay
accurate, and scheduling revision on evidence rather than on a calendar. Those
are database, algorithm and architecture problems. The language model is a
component within them, behind an interface, replaceable.

The most instructive part of the work was not building the personalization but
hardening it. A system that produced good explanations and served every
learner's private conversation to anyone who asked would have looked complete
in a demonstration. Four such defects existed, and none was found by a scanner —
CodeQL had nothing to say, because authorisation policy is not inferable from
source code. They were found by reading the code asking who is permitted to do
this, which is a question only a person can pose. That is the lesson the project
would most want to record.

{{PAGEBREAK}}
