# CHAPTER 1: INTRODUCTION

## 1.1 Overview of the Project

The Adaptive Learning Platform is a web-based tutoring system for Data
Structures and Algorithms that adapts its teaching to the individual learner. A
learner signs up, states how they prefer to be taught, and sits a short
placement quiz. From that point the system maintains a model of them — what
they have mastered, what they struggle with, and how they respond to different
kinds of explanation — and conditions every subsequent interaction on it.

The application is a React single-page frontend over a FastAPI backend and a
PostgreSQL database, using a hosted large language model for generation. It
covers the full learning loop: a conversational tutor, on-demand quizzes, a
knowledge graph tracking per-concept mastery, and a spaced-repetition schedule
that brings weak concepts back for review.

What separates it from a chat interface placed in front of a language model is
that the personalization is *architectural*. The learner model lives in the
database, is assembled into every prompt by a dedicated prompt-building layer,
and is exposed back to the learner through the interface. Chapter 2 details
each of the four mechanisms involved.

## 1.2 Problem Statement and Motivation

### The problem

Self-directed learners studying Data Structures and Algorithms have no shortage
of material. Platforms such as Brilliant, Codecademy and YouTube offer large,
well-produced catalogues. What they share is a fixed presentation: the
explanation of recursion is the same explanation regardless of who is reading
it.

This creates two failure modes. A learner who needs a worked example before an
abstract definition may bounce off a theory-first treatment and conclude the
topic is beyond them. A learner who already understands the abstraction wastes
time on motivating examples they did not need. Neither is a content-quality
problem; both are a fit problem.

Three specific gaps follow:

1. **No memory across sessions.** A returning learner starts from zero. The
   platform does not know what confused them last week.
2. **No adaptive difficulty.** Content is authored at one level. The learner
   must self-select, without reliable information about their own competence.
3. **No individual model.** Progress tracking is typically completion-based —
   videos watched, exercises attempted — rather than a model of what the
   learner actually understands.

### Motivation

Benjamin Bloom's "2 Sigma" study [1] found that students taught one-to-one
performed roughly two standard deviations above conventionally taught students —
the median tutored learner outperforming ninety-eight percent of the control
group. Bloom framed the finding as a problem to be solved: one-to-one tutoring
does not scale economically, so the task is to find scalable methods that
approach its results.

Much of the tutor's advantage comes from behaviours that are, in principle,
mechanisable: continuously assessing understanding, adjusting explanation to the
individual, and returning to weak material at the right interval. Large language
models make the generation side tractable. The engineering problem is the rest —
maintaining a durable learner model, deciding what to teach next, grounding
generated content so it stays accurate, and scheduling revision. That problem is
the subject of this project.

### Why it matters

Data Structures and Algorithms is a compulsory, heavily assessed subject, and a
common point of attrition in computer science programmes. Its concepts are
strongly ordered: a learner who has not internalised recursion will not follow
tree traversal, and one shaky on time complexity cannot evaluate why one sorting
algorithm is preferred over another. Prerequisite structure of this kind is
precisely what a knowledge graph can represent and a fixed linear syllabus
cannot.

## 1.3 Objectives of the Capstone

The project set out to deliver the following.

**O1 — Model the learner explicitly.** Persist learning style, pace, detail
level and code-complexity preferences, and maintain per-concept mastery scores
derived from actual performance rather than self-report.

**O2 — Condition every generated response on that model.** Assemble prompts
from modular blocks so that profile, cross-session memory and retrieved
reference material all shape the output.

**O3 — Give the tutor durable memory.** Maintain a natural-language summary of
how the learner thinks, revised automatically as the conversation progresses and
carried across sessions.

**O4 — Ground generation in reference material.** Use vector similarity search
over embedded explanations so the tutor draws on stored material rather than
generating freely, reducing the scope for confident errors.

**O5 — Represent the subject as a prerequisite graph.** Model DSA as concepts
with typed dependencies, and use mastery of prerequisites to gate and recommend
what comes next.

**O6 — Schedule revision on evidence.** Apply the SM-2 algorithm to quiz
outcomes so review intervals expand on success and reset on failure.

**O7 — Make the adaptation visible.** Surface the specific signals that shaped
each response, so personalization is demonstrable to the learner rather than
asserted.

**O8 — Engineer it as a deployable system.** Layered architecture, migrations,
automated tests, a CI pipeline including security scanning, and a documented
path to cloud deployment.

## 1.4 Scope of Implementation

### In scope

| Area | Delivered |
|---|---|
| Subject domain | Data Structures and Algorithms — 25 concepts, 37 typed edges, 5 difficulty tiers |
| Accounts | Email and password sign-up, bcrypt hashing, JWT sessions |
| Onboarding | Preference capture plus a 10-question placement quiz seeding initial mastery |
| Tutoring | Multi-session conversational chat with markdown and syntax-highlighted code |
| Assessment | LLM-generated multiple-choice quizzes targeting the learner's weak areas |
| Progress | Per-concept mastery, prerequisite unlocking, next-concept recommendation |
| Revision | SM-2 scheduling with a dedicated review queue |
| Transparency | Per-message record of the personalization signals applied |
| Profile management | View and edit preferences; view accumulated tutor memory |
| Engineering | 24 REST endpoints, 13 tables, 133 automated tests, 5-stage CI, cloud deployment configuration |

### Out of scope

Deliberately excluded, with reasons:

- **Subjects beyond DSA.** The schema is subject-agnostic — `concept_nodes`
  carries a `subject` column — but only the DSA graph is authored. Adding
  another subject is a data exercise, not a code change.
- **Code execution.** The tutor explains and quizzes; it does not run learner
  code. A sandboxed judge is a substantial subsystem in its own right.
- **Free-text answer grading.** Assessment is multiple-choice, which is
  objectively gradable. Grading free-form answers with an LLM introduces a
  reliability problem the project does not attempt to solve.
- **Multi-user features.** No cohorts, leaderboards or instructor dashboards.
  The system models one learner at a time.
- **Native mobile applications.** The interface is responsive; there is no
  native client.
- **Model fine-tuning.** Personalization is achieved through prompt
  construction and retrieval, not by training a model.

### Assumptions and constraints

- Groq's free tier imposes rate limits, which shapes the content seeder's
  pacing and the decision to cap retrieved chunks at two or three per request.
- Free-tier cloud hosting caps image size, so the deployed backend omits the
  local embedding model and RAG grounding is unavailable in the cloud
  deployment. The system degrades to profile-driven personalization rather than
  failing. This is discussed in sections 4.4 and 6.3.
- Evaluation is functional. Measuring learning gain would require a controlled
  study with human participants, which is outside the scope of this submission.

## 1.5 Organization of the Report

**Chapter 2 — Implementation Details** presents the system architecture, data
flow and component interaction; the technology stack and the reasoning behind
each choice; a module-by-module description; the key algorithms in pseudocode,
covering mastery estimation, SM-2 scheduling, prerequisite unlocking, prompt
assembly and structured-output recovery; and annotated screenshots and code.

**Chapter 3 — Testing, Validation and Results** sets out the testing strategy
and tooling, the test-case matrix with outcomes, and analysis of the results,
including the four access-control defects found during development.

**Chapter 4 — Execution and Deployment** covers the execution environments,
local and cloud deployment procedures, and the differences between them.

**Chapter 5 — Project Execution Evidence** records the repository, the commit
history, the weekly progress log and the supervisor interactions.

**Chapter 6 — Conclusion and Future Work** summarises what was built, states
the limitations honestly, and identifies the extensions the architecture is
positioned for.

{{PAGEBREAK}}
