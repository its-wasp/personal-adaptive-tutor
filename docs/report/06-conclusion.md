# CHAPTER 6: CONCLUSION AND FUTURE WORK

## 6.1 Summary of Implementation

We built a working adaptive tutoring platform for Data Structures and
Algorithms: a React frontend over a FastAPI backend, a PostgreSQL database with
vector search, and a hosted language model.

The system is roughly 9,900 lines across 130 files. It has 24 REST endpoints, 13
tables, 3 migrations, 25 concepts with 37 prerequisite edges, and 133 automated
tests behind a five-job CI pipeline.

The substance is not the chat interface but the four mechanisms behind it. The
learner profile is turned into instructions in every system prompt. A
natural-language memory is updated by the model every five messages and carried
between sessions. Retrieved reference material grounds the explanations. A
prerequisite graph tracks mastery, which gates progression, targets questions
and drives the revision schedule.

## 6.2 Achievements Against Objectives

| # | Objective | Outcome |
|---|---|---|
| O1 | Model the learner explicitly | Met. Preferences across five dimensions, mastery derived from actual performance |
| O2 | Condition responses on that model | Met. Modular prompt assembly on every generation |
| O3 | Memory across sessions | Met. Updated every five messages, merged rather than replaced |
| O4 | Ground generation in reference material | Met locally, degraded in production. See 6.3 |
| O5 | Prerequisite graph | Met. 25 concepts, 37 edges, unlocking at 0.6 mastery |
| O6 | Evidence-based revision | Met. SM-2 driven by quiz results, with a review queue |
| O7 | Make adaptation visible | Met. Signals recorded at generation time and shown per message |
| O8 | Deployable engineering | Met. Layered architecture, migrations, 133 tests, CI with security scanning |

Beyond the stated objectives, the security review found and fixed four access
control bugs that would have let any signed-in learner read and modify another
learner's data. That is covered in section 3.3.3.

## 6.3 Limitations

**RAG is not available in the deployed version.** The embedding model needs
PyTorch, which pushes the image past the free tier's size limit. The
architecture handles this cleanly, but it means the deployed system demonstrates
three of the four personalization mechanisms rather than all four. Paid hosting
or a hosted embedding API would fix it.

**We did not measure effectiveness.** We can show the system is adaptive, in
that it produces different explanations of the same concept for different
profiles. Whether that actually improves learning is unknown and would need a
controlled study over several weeks.

**Mastery rests on multiple-choice evidence.** A learner can get the right
answer by elimination, and four options sample a concept narrowly. The mastery
number is noisier than it looks. The confidence field records how much evidence
is behind it, but nothing currently uses that.

**Only one subject.** The schema is subject-agnostic and every query filters on
subject, but only the DSA graph exists. The claim that adding another subject is
just data is reasonable but untested.

**Test coverage is uneven.** 60% on the backend, 13.7% on the frontend, and no
automated test touches a real database.

**No concurrency handling.** `get_or_create_profile` and similar
read-then-create patterns would race if two requests arrived at once for the
same new user. A single user never hits this; thirty students starting together
might.

## 6.4 Future Enhancements

**Stream the responses.** Replies take two to six seconds, almost all of it
model latency, and the interface just shows "Tutor is thinking…" for the whole
time. Groq supports server-sent events and FastAPI supports streaming
responses. Perceived latency would drop to a few hundred milliseconds. This is
the biggest available improvement and needs no architectural change.

**Free-text answers.** The best evidence of understanding is an explanation in
the learner's own words. Grading that against a model-generated rubric would
give a much better mastery signal than multiple choice, though the reliability
of the grading would need work.

**Use the confidence value.** It is calculated and stored and nothing reads it.
A mastery of 0.8 from two answers should not unlock as much as 0.8 from twenty.
That is a small change to one condition with a real effect on pacing.

**Add a second subject.** The most direct test of whether the graph model is
actually general.

**Adaptive question difficulty.** Quizzes currently take their difficulty from
the session level. Choosing per question based on current mastery would keep the
learner closer to the edge of what they know.

**Learner-facing analytics.** Engagement events are recorded on every
interaction and only the streak uses them. Time-of-day patterns and per-concept
time are already in the table and unqueried.

**A test database in CI.** A throwaway Postgres service container would let the
repository tests run against real SQL and close the biggest gap in our testing.

## 6.5 Concluding Remarks

Bloom framed one-to-one tutoring as a target to aim for rather than a curiosity.
Language models make the generation half of that problem almost easy. What this
project suggests is that generation was never the hard part.

The hard part is what makes a tutor's advice personal: keeping a model of the
learner that survives between sessions, deciding what to teach next from what
they have actually demonstrated, grounding explanations so they stay accurate,
and scheduling revision on evidence rather than on a calendar. Those are
database, algorithm and architecture problems. The language model sits inside
them as one replaceable component.

The most useful part of the work for us was not building the personalization but
hardening it afterwards. A system that gave good explanations and also served
every learner's private conversation to anyone who asked would have looked
finished in a demo. There were four such bugs, and no scanner found any of them.
CodeQL had nothing to say, because authorisation policy is not something you can
read off the source. They were found by sitting down and asking who is allowed
to do this, which is still a question a person has to ask.

{{PAGEBREAK}}
