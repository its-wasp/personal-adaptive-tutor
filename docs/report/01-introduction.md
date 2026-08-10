# CHAPTER 1: INTRODUCTION

## 1.1 Overview of the Project

The Adaptive Learning Platform is a web-based tutor for Data Structures and
Algorithms that adapts what it teaches to the individual learner. A user signs
up, says how they prefer to be taught, and takes a short placement quiz. From
then on the system keeps a model of what they know and how they learn, and uses
it to shape every explanation and quiz question.

It is built as a React single-page application over a FastAPI backend and a
PostgreSQL database, with a hosted language model doing the text generation. The
application covers a full learning loop: a chat-based tutor, on-demand quizzes,
a knowledge graph that tracks mastery per concept, and a revision schedule that
brings weak topics back for review.

The part we care about is that the personalization is built into the system
rather than added as a prompt instruction. The learner model lives in the
database, a dedicated prompt-building layer assembles it into every request, and
the interface shows the learner which parts of their profile were used.

## 1.2 Problem Statement and Motivation

Learners studying DSA have plenty of material available. Brilliant, Codecademy
and YouTube all have large, well-made catalogues. What they have in common is
that the content is fixed: the explanation of recursion is the same no matter
who reads it.

That causes two problems. A learner who needs a worked example before an
abstract definition may give up on a theory-first treatment and decide the topic
is beyond them. A learner who already understands the abstraction wastes time on
motivating examples. Neither is a problem with content quality. It is a problem
of fit.

Three gaps follow from this:

1. **No memory between sessions.** A returning learner starts from scratch. The
   platform does not know what confused them last week.
2. **No adaptive difficulty.** Content is written at one level and the learner
   has to pick for themselves, without much information about their own level.
3. **No model of the learner.** Progress is usually tracked by completion,
   videos watched or exercises attempted, not by what the learner understands.

Bloom's "2 Sigma" study [1] found that students taught one-to-one performed
about two standard deviations better than students in conventional classrooms.
Bloom presented this as a problem to solve rather than a curiosity: one-to-one
tutoring does not scale, so the task is to find scalable methods that get close
to it.

A lot of what a tutor does can in principle be automated. Checking whether the
student has understood, adjusting the explanation, and coming back to weak
material at the right time are all mechanical in nature. Language models make
the generation part easy. The remaining work is keeping a learner model,
deciding what to teach next, grounding the content so it stays accurate, and
scheduling revision. That is what this project tries to do.

DSA is a reasonable subject to try it on. It is compulsory in most computer
science programmes and a common point where students struggle. Its topics are
also strongly ordered: someone who has not understood recursion will not follow
tree traversal. That kind of prerequisite structure is something a graph can
represent and a linear syllabus cannot.

## 1.3 Objectives of the Capstone

| # | Objective |
|---|---|
| O1 | Store an explicit learner profile, and derive per-concept mastery from actual quiz performance rather than self-assessment |
| O2 | Use that profile to shape every generated response |
| O3 | Maintain a memory of the learner that carries across sessions |
| O4 | Ground generated explanations in stored reference material |
| O5 | Model DSA as a graph of concepts with prerequisite relationships |
| O6 | Schedule revision based on quiz results using a spaced repetition algorithm |
| O7 | Show the learner which signals shaped each response |
| O8 | Build it as a deployable system with tests, CI and documented deployment |

## 1.4 Scope of Implementation

**Included:**

- 25 DSA concepts across 5 difficulty tiers, with 37 prerequisite edges
- Email and password accounts with bcrypt hashing and JWT sessions
- Onboarding: preference capture plus a 10-question placement quiz
- Chat-based tutoring with markdown and syntax-highlighted code
- Generated multiple-choice quizzes aimed at the learner's weak areas
- Per-concept mastery, prerequisite unlocking, next-concept recommendation
- SM-2 revision scheduling with a review queue
- A per-message record of the personalization signals applied
- Profile page for editing preferences and viewing the tutor's memory
- 24 REST endpoints, 13 tables, 133 automated tests, 5-job CI pipeline

**Not included, and why:**

- **Other subjects.** The schema is subject-agnostic, but only the DSA graph is
  written. Adding another subject is a data task, not a code change.
- **Code execution.** The tutor explains and quizzes but does not run learner
  code. A sandboxed judge is a large piece of work on its own.
- **Free-text answer grading.** Assessment is multiple-choice because it can be
  graded objectively. Grading written answers with an LLM brings a reliability
  problem we did not attempt to solve.
- **Multi-user features.** No cohorts, leaderboards or instructor views.
- **Model fine-tuning.** Personalization is done through prompt construction and
  retrieval, not training.

**Constraints we worked under:**

Groq's free tier has rate limits, which is why the content seeder paces itself
and why retrieval is capped at two or three chunks per request. Free cloud
hosting limits image size, so the deployed backend leaves out the local
embedding model and runs without RAG grounding. It falls back to profile-based
personalization instead of failing. This is discussed in sections 4.4 and 6.3.

Evaluation is functional. Measuring whether the system actually improves
learning would need a controlled study with real students over several weeks,
which was not possible in the time available.

## 1.5 Organization of the Report

Chapter 2 covers the architecture, technology choices, module breakdown and the
main algorithms, with screenshots and code. Chapter 3 covers the test plan, test
cases and results, including the security issues found during development.
Chapter 4 covers how to run and deploy the system. Chapter 5 contains the
version control evidence and weekly progress log. Chapter 6 summarises what was
built, what its limitations are, and what could be added next.

{{PAGEBREAK}}
