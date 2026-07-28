# Diagrams

Source for every figure in the capstone report. Written as Mermaid (`.mmd`)
rather than binary images so they stay diffable, reviewable and editable
alongside the code they describe.

## The figures

| File | Figure | Shows |
|---|---|---|
| `architecture.mmd` | 2.1 | Deployment tiers, the personalization subsystem, and external services |
| `dfd-level-0.mmd` | 2.2a | Context diagram — the system as one process |
| `dfd-level-1.mmd` | 2.2b | Six major processes and the data stores between them |
| `component-interaction.mmd` | 2.3 | Router → service → repository layering |
| `er-model.mmd` | 2.4 | All 13 tables and their relationships |
| `sequence-chat.mmd` | 2.5 | A personalized chat turn, start to finish |
| `sequence-quiz-mastery.mmd` | 2.6 | Quiz submission through mastery update and SM-2 rescheduling |

## Viewing

GitHub renders `.mmd` in the file view directly — open any of them in the web
UI and you get the diagram, no tooling needed.

## Exporting to PNG for the report

`build_report.py` embeds images through python-docx, which cannot read SVG, so
the report needs PNG. Pick whichever route suits:

**mermaid.live** (no install)
1. Open <https://mermaid.live>
2. Paste the contents of a `.mmd` file
3. **Actions → PNG**, and save into `docs/screenshots/` using the filename the
   report expects (listed in `docs/screenshots/SCREENSHOT-CHECKLIST.md`)

Set the export scale to 2x or higher. The default rasterises small enough to
blur in print.

**mermaid-cli** (batch, needs Node and a Chromium download)
```bash
npm install -g @mermaid-js/mermaid-cli
cd docs/diagrams
for f in *.mmd; do mmdc -i "$f" -o "../screenshots/${f%.mmd}.png" -s 3 -b white; done
```

Use `-b white` either way. A transparent background disappears against a white
page in Word.

## Editing

Keep the `---\ntitle: ...\n---` front matter: it carries the figure number, so
the numbering in the report and in the source can't drift apart. If you add a
diagram, add a row to the table above and to the report's List of Figures.
