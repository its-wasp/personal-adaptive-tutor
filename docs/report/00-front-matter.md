<!-- COVER -->

# {{title}}

**A Capstone Project Report**

{{students_block}}

**Program:** {{program}}

**Institution:** {{institution}}

**Academic Year:** {{academic_year}}

**Internal Supervisor:** {{supervisor}}

**Date of Submission:** {{submission_date}}

{{PAGEBREAK}}

## Declaration

We hereby declare that this capstone project titled "{{title}}" is an original
work carried out by us and has not been submitted to any other university or
institution for the award of any degree.

All libraries, services and reference material used have been cited in the
References section. The complete source code and commit history are available
at {{github_url}}.

{{students_signature_block}}

{{PAGEBREAK}}

## Abstract

Most self-study platforms for Data Structures and Algorithms give every learner
the same explanation. A student who learns best from worked examples gets the
same page as one who prefers a formal definition. This project builds a tutoring
platform that keeps a model of the individual learner and uses it to shape every
response.

The system is a web application with a React frontend and a FastAPI backend over
PostgreSQL. Personalization works through four mechanisms. A learner profile
stores style, pace and detail preferences, which the prompt builder turns into
instructions for the language model. A natural-language summary of the learner
is updated by the model every five messages and carried into later sessions.
Retrieval-augmented generation grounds explanations in reference material stored
as vectors using pgvector. A knowledge graph of 25 DSA concepts tracks
per-concept mastery, which controls prerequisite unlocking, targets quiz
questions at weak areas, and drives an SM-2 spaced repetition schedule. Text
generation uses Groq's openai/gpt-oss-20b behind a provider interface.

One feature we think is unusual: every tutor reply stores a record of which
profile signals shaped it, shown in the interface as an expandable "Why this
response" note. This makes the personalization visible rather than something the
learner has to take on trust.

The finished system has 24 REST endpoints over 13 tables, 133 automated tests,
and a CI pipeline running lint, static analysis, dependency auditing and
container scanning. A security review during development found and fixed four
access control bugs that let any signed-in user read another user's data.

{{PAGEBREAK}}

{{TOC}}

{{PAGEBREAK}}

{{LOF}}

{{PAGEBREAK}}

{{LOT}}

{{PAGEBREAK}}

## List of Abbreviations

| Abbreviation | Expansion |
|---|---|
| API | Application Programming Interface |
| CI | Continuous Integration |
| CORS | Cross-Origin Resource Sharing |
| CRUD | Create, Read, Update, Delete |
| DFD | Data Flow Diagram |
| DSA | Data Structures and Algorithms |
| DTO | Data Transfer Object |
| ER | Entity-Relationship |
| IDOR | Insecure Direct Object Reference |
| JSON | JavaScript Object Notation |
| JWT | JSON Web Token |
| LLM | Large Language Model |
| MCQ | Multiple Choice Question |
| ORM | Object-Relational Mapping |
| RAG | Retrieval-Augmented Generation |
| REST | Representational State Transfer |
| SAST | Static Application Security Testing |
| SCA | Software Composition Analysis |
| SM-2 | SuperMemo 2 spaced repetition algorithm |
| SPA | Single-Page Application |
| UUID | Universally Unique Identifier |

{{PAGEBREAK}}
