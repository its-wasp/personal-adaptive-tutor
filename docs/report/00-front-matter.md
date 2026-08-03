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

All external libraries, services and reference materials used in the course of
this work have been cited in the References section. The source code in its
entirety, together with its complete commit history, is available at
{{github_url}}.

{{students_signature_block}}

{{PAGEBREAK}}

## Abstract

Existing self-study platforms for Data Structures and Algorithms deliver the
same explanation to every learner. A student who reasons best from concrete
examples and struggles with recursion receives identical material to one who
prefers formal definitions and finds recursion straightforward. This project
addresses that gap by building an adaptive tutoring platform that models the
individual learner and conditions every response on that model.

The system is a full-stack web application. A FastAPI backend organised into
router, service and repository layers exposes twenty-four REST endpoints over a
PostgreSQL database of thirteen tables, with pgvector providing similarity
search. A React 19 single-page application consumes it. Personalization is
implemented as four cooperating mechanisms: an explicit learner profile
capturing style, pace and detail preferences; an evolving natural-language
memory that the language model revises every five messages and that is injected
into subsequent prompts; retrieval-augmented generation that grounds
explanations in embedded reference material using a local sentence-transformers
model; and a twenty-five node knowledge graph whose per-concept mastery scores
drive prerequisite unlocking, question targeting and an SM-2 spaced-repetition
schedule. Groq's llama-3.1-8b-instant performs generation behind a
provider-agnostic interface.

A distinguishing feature is transparency. Each assistant response carries a
persisted snapshot of the profile signals that shaped it, surfaced in the
interface as an expandable "Why this response" indicator, making the adaptation
visible rather than merely claimed.

The delivered system passes 133 automated tests across backend and frontend,
an end-to-end smoke suite covering every endpoint, and a five-stage CI pipeline
performing linting, static analysis, dependency auditing and container
scanning. A security review conducted during development identified and closed
four broken-access-control defects.

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
| BFS | Breadth-First Search |
| CDN | Content Delivery Network |
| CI | Continuous Integration |
| CORS | Cross-Origin Resource Sharing |
| CRUD | Create, Read, Update, Delete |
| CVE | Common Vulnerabilities and Exposures |
| DFD | Data Flow Diagram |
| DFS | Depth-First Search |
| DSA | Data Structures and Algorithms |
| DTO | Data Transfer Object |
| EF | Ease Factor (SM-2 algorithm) |
| ER | Entity-Relationship |
| HTTP | HyperText Transfer Protocol |
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
| SM-2 | SuperMemo 2 spaced-repetition algorithm |
| SPA | Single-Page Application |
| SQL | Structured Query Language |
| UUID | Universally Unique Identifier |

{{PAGEBREAK}}
