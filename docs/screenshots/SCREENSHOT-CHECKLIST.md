# Screenshot and Figure Capture Checklist

Everything the report needs that cannot be generated from the repository.
Save each file into this directory using the exact filename given — the report
references them by that name.

## Before you start

Have a **seeded account with real history**. Empty-state screenshots make the
system look unfinished, and several figures are meaningless without data. Ten
minutes of setup:

1. Sign up and complete onboarding, answering the placement quiz honestly
   (roughly half correct gives the most interesting graph — some concepts
   green, some amber, some locked).
2. Start two or three sessions from different concepts and hold a short
   conversation in each, at least six messages, so the learner memory has been
   generated at least once.
3. Answer several quizzes, deliberately getting some wrong. Correct answers
   raise mastery and unlock dependent concepts; wrong answers populate the
   review queue.
4. Optionally run the content seeder first, so "Grounded" appears among the
   personalization reasons:
   `docker compose exec backend python -m app.rag.content_seeder`

**Capture settings.** Browser at 1440px wide or more, at 100% zoom, in light
mode. Hide bookmarks and any browser extensions. PNG, not JPEG — screenshots
of text compress badly as JPEG.

## Application screenshots

| File | Figure | What to show |
|---|---|---|
| `fig-2.7-onboarding-preferences.png` | 2.7 | Onboarding step 1, with a learning style and pace visibly selected |
| `fig-2.8-onboarding-placement.png` | 2.8 | Onboarding step 2, mid-quiz, with the question counter and tier visible |
| `fig-2.9-dashboard.png` | 2.9 | Full dashboard. Must show varied mastery bars, at least one padlock, the recommendation card and the progress summary |
| `fig-2.10-concept-detail.png` | 2.10 | A concept selected, right-hand panel open, showing mastery, prerequisites and the level selector |
| `fig-2.11-chat-session.png` | 2.11 | A tutor reply containing both prose and a syntax-highlighted code block |
| `fig-2.12-why-this-response.png` | 2.12 | The "Why this response" pill **expanded**, showing three or four reasons. The single most important screenshot in the report |
| `fig-2.13-quiz-answered.png` | 2.13 | A quiz after an **incorrect** answer, so the green correct option, the red wrong pick, the hint and the explanation are all visible at once |
| `fig-2.14-review-queue.png` | 2.14 | Review page with at least two concepts due, showing intervals and overdue badges |
| `fig-2.15-profile.png` | 2.15 | Profile page with the tutor memory card populated — this needs a session of at least six messages |
| `fig-2.16-personalization-comparison.png` | 2.16 | See below |

### Figure 2.16 — the comparison shot

This is the figure that evidences the project's central claim, so it is worth
the extra effort.

1. Set your profile to **Example-first**, start a session on Recursion, and
   screenshot the opening explanation.
2. Change the profile to **Theory-first** and start a *new* session on
   Recursion.
3. Screenshot that opening explanation.
4. Place the two side by side in one image, labelled.

The two should differ visibly in structure: one opening with code, the other
with the definition. If they look the same, say so in the report rather than
picking a more flattering pair — a negative result honestly reported is worth
more than a cherry-picked one.

## Diagram exports

The seven Mermaid diagrams in `docs/diagrams/` need exporting to PNG, since
python-docx cannot embed SVG. Easiest route is <https://mermaid.live>: paste
the `.mmd` contents, then **Actions → PNG**. Set scale to 2x or higher, and use
a white background — a transparent one vanishes against a white page.

| File | Figure | Source |
|---|---|---|
| `fig-2.1-architecture.png` | 2.1 | `diagrams/architecture.mmd` |
| `fig-2.2a-dfd-level-0.png` | 2.2a | `diagrams/dfd-level-0.mmd` |
| `fig-2.2b-dfd-level-1.png` | 2.2b | `diagrams/dfd-level-1.mmd` |
| `fig-2.3-component-interaction.png` | 2.3 | `diagrams/component-interaction.mmd` |
| `fig-2.4-er-model.png` | 2.4 | `diagrams/er-model.mmd` |
| `fig-2.5-sequence-chat.png` | 2.5 | `diagrams/sequence-chat.mmd` |
| `fig-2.6-sequence-quiz-mastery.png` | 2.6 | `diagrams/sequence-quiz-mastery.mmd` |

The ER diagram is wide. Export it at high scale and consider landscape
orientation for that page in Word.

## Repository evidence

| File | Figure | What to show |
|---|---|---|
| `fig-5.1-commit-history.png` | 5.1 | The repository commit list, showing the spread of commits across the development window |
| `fig-5.2-contributors.png` | 5.2 | GitHub **Insights → Contributors**, showing all three members |
| `fig-5.3-ci-pipeline.png` | 5.3 | A green Actions run with all five jobs passing |

## Also needed

These are not screenshots but are the remaining gaps in the report:

- [ ] Fill in `docs/report/report-meta.json` — roll numbers, institution,
      academic year, supervisor name, submission date
- [ ] Record the demo video and add its URL to `report-meta.json`
      (contents are listed in Appendix D)
- [ ] Deploy, and add the frontend and backend URLs to `report-meta.json`
- [ ] Complete the supervisor interaction table in
      `docs/report/05-evidence.md` section 5.3
- [ ] Add page numbers to the Roman-numeral front matter if your institution
      requires them separately from the Arabic body numbering

## Inserting images into the report

The current chapters carry figure captions but no image references, because
the files do not exist yet. Once they do, add an image line directly above each
caption, for example:

```markdown
![](../screenshots/fig-2.9-dashboard.png)

> **Figure 2.9 — Dashboard.** Twenty-five concepts in five tiers...
```

Then extend `build_report.py`'s `parse_blocks` to emit an `image` block for
`![](path)` and `render_block` to call `doc.add_picture(path,
width=Inches(6))`. It is roughly ten lines; the parser is deliberately small
so that additions like this are easy.

Alternatively, insert the images by hand in Word after building — acceptable
for a one-off submission, though it has to be redone on every rebuild.
