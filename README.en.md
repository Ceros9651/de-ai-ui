# de-ai-ui

[日本語](README.md)

**A Claude Code agent and skill that finds the "AI-generated look" in your frontend and fixes it using real apps as references.**

Rounded cards everywhere, icons and emoji on every label, purple-to-blue gradients, the same padding and centered text on every section. Screens built by generative AI tend to look like this.

Running `/ui-review <screen>` does the following:

1. Compares the screen's code with the rendered page (Playwright screenshots and computed-style measurements) and reports up to 5 issues, most important first.
2. For each issue, offers 2–3 fixes based on what real apps do, as multiple-choice questions (with a recommended option, a preview, and the impact on other screens; "leave as is" is always an option).
3. Files the chosen fixes as a change plan (an OpenSpec change, or proposal / tasks under `docs/ui-reviews/`).
4. Records each adopted decision as a one-line rule in `docs/design-principles.md`, so later reviews and new screens follow it.

After implementing, `/ui-review --verify <change>` takes after-screenshots, compares them with the before-screenshots, and judges each task. It also checks for new "AI look" introduced by the fix and for side effects (overflow, contrast, tap targets, and so on).

The goal is not to strip decoration. It is to make the screen match **the weight of its information and the flow of its tasks**. Fixes that only remove decoration and make the screen harder to use are not proposed.

## What it detects

| Category                         | Examples                                                                       |
| -------------------------------- | ------------------------------------------------------------------------------ |
| Overused rounded cards           | Every kind of information wrapped in the same rounded box; nested cards        |
| Decorative icons and emoji       | Icons that repeat their label; emoji in navigation                             |
| Gradients, shadows, meaningless color | Purple-blue gradients; shadows on everything; semantic colors used as decoration |
| Uniform spacing and centering    | Same spacing everywhere; centered numbers; key totals below the fold          |
| Principle violations             | Anything that breaks a rule recorded in `docs/design-principles.md`           |

See [anti-patterns.md](.claude/skills/ui-review/anti-patterns.md) for the full criteria. The instruction files are written in Japanese; Claude reads them fine, and you can talk to it in English.

## Requirements

- [Claude Code](https://claude.com/claude-code)
- Node.js (Playwright MCP is started with `npx`)
- A web frontend with a dev server (React / Vue / Svelte, etc.; plain CSS, Tailwind, CSS Modules, or a UI library)
- Optional: [OpenSpec](https://github.com/Fission-AI/OpenSpec). If your repo uses it, fixes are filed as changes; otherwise they go to `docs/ui-reviews/`.

## Install

Run this at the root of your app repository:

```sh
git clone --depth 1 https://github.com/Ceros9651/de-ai-ui.git /tmp/de-ai-ui
mkdir -p .claude
cp -r /tmp/de-ai-ui/.claude/. ./.claude/
```

1. Add the `playwright` server to `.mcp.json` (if you already have one, add only the `playwright` entry under `mcpServers`):

   ```json
   {
     "mcpServers": {
       "playwright": {
         "command": "npx",
         "args": ["@playwright/mcp@latest", "--isolated", "--output-dir", ".ui-review-tmp"]
       }
     }
   }
   ```

2. Add the temporary screenshot folder to `.gitignore`:

   ```
   .ui-review-tmp/
   ```

3. Optionally, make new screens follow the same rules by adding this to `CLAUDE.md`:

   ```markdown
   ## UI design

   When creating or changing frontend screens or components, read and follow `docs/design-principles.md`.
   Avoid overused rounded cards, decorative icons and emoji, gradients and heavy shadows, and uniform spacing with centered layouts (see `.claude/skills/ui-review/anti-patterns.md`).
   ```

4. Restart Claude Code and allow the `playwright` MCP server. The first run may download a browser.

## Usage

```text
/ui-review home                        Review a screen → choose fixes → file a change plan
/ui-review --verify ui-refine-home     After implementing, verify with before/after screenshots
```

On the first run, two setup steps happen first:

- **Project setup**: it inspects your repo and writes the screen list, URLs, styling approach, viewports, how to prepare data, and where to file changes to `.claude/skills/ui-review/project.md`, then asks you to confirm.
- **Reference apps**: it proposes real apps in the same genre; the ones you pick are saved to `references.md`.

Implement the filed plan with your usual workflow (for example `/opsx:apply` with OpenSpec). The agent never edits your app code during a review.

## Layout

```
.claude/
  agents/ui-reviewer.md              Analysis subagent (reads code, screenshots, measures, proposes; never edits)
  skills/ui-review/
    SKILL.md                         The /ui-review workflow (setup, consultation, filing, verification)
    anti-patterns.md                 Detection criteria (4 categories + principle violations)
    references.md                    Curated reference apps (picked on the first run)
    templates/project.md             Project settings template (filled in as project.md on the first run)
    templates/design-principles.md   Design principles template
  agents/pptx-reviewer.md            Deck analysis subagent (reads extracted structure and slide images, proposes; never edits)
  skills/pptx-review/
    SKILL.md                         The /pptx-review workflow (extract, consult, apply, verify, export)
    anti-patterns.md                 Deck detection criteria (5 categories + principle violations)
    references.md                    Curated reference decks and guides (picked on the first run)
    templates/slide-principles.md    Slide principles template
    scripts/                         Extraction (extract.py), rendering (render.py), sample deck (make_sample.py)
input/                               Put the .pptx to review here (contents are git-ignored)
output/                              Revised decks and reports (contents are git-ignored)
.mcp.json                            Example Playwright MCP config
```

## Design decisions

- Subagents cannot ask the user questions, so analysis (`ui-reviewer`) and consultation (AskUserQuestion in the main conversation) are separated.
- At most 5 issues per review. The rest are summarized and can be left for the next review.
- Only real, shipping apps are used as references — no template marketplaces, concept shots, or AI-generated showcases.
- The screenshot browser runs with `--isolated` and never touches the user's own data. For screens that would otherwise be empty, describe how to load test data under "データの準備" (data preparation) in `project.md`.
- `/ui-review` runs only when you invoke it explicitly (`disable-model-invocation: true`).

## Reviewing PowerPoint decks (/pptx-review)

Everyday PowerPoint decks show the same "AI look": three rounded cards with icons in a row, emoji in headings, purple-to-blue gradient backgrounds with drop shadows, body text centered, and phrases like "innovative", "seamless", "empower". `/pptx-review` finds these and writes out a revised .pptx.

```text
/pptx-review proposal.pptx     Review input/proposal.pptx → choose fixes → write the revised deck to output/
/pptx-review                   Pick a .pptx from input/
```

1. Put the deck you want reviewed in `input/` (one file per run).
2. It cross-checks the deck's structure (fills, shadows, corner radius, alignment, text, slide master and theme) against rendered slide images, groups issues of the same kind, and reports up to 5 in order of impact.
3. For each issue you choose a fix from multiple-choice options. When the cause is in the slide master or theme, you get both a fix there (marked "affects all slides") and a fix limited to the affected slides.
4. Chosen fixes are applied, then the result is rendered and checked for missed fixes, text overflow, overlaps, contrast, and newly introduced AI look before it is written out.
5. Adopted rules are recorded one per line in `docs/slide-principles.md` and carried over to the next review.

Output (the original in `input/` is never modified):

```text
output/
  proposal-reviewed.pptx       Revised deck
  proposal-reviewed/
    report.md                  Issues, chosen fixes, what changed, verification
    before-<n>.png / after-<n>.png   Before/After of the changed slides
```

It fixes slide design and the visible text on slides. Speaker notes, animations, and pictures/photos/logos are left untouched. Rewrites keep numbers and proper nouns as they are and never invent numbers.

### Requirements for /pptx-review

- Python 3 and [python-pptx](https://python-pptx.readthedocs.io/) (`pip install python-pptx`)
- One of the following to render slides:
  - Microsoft PowerPoint (Windows desktop). Used first when available.
  - [LibreOffice](https://www.libreoffice.org/) (`soffice` on PATH), plus PyMuPDF (`pip install pymupdf`) or poppler's `pdftoppm` to turn the PDF into images

Playwright MCP is not needed.

### Installing /pptx-review

Copy `.claude/` as for `/ui-review`, create `input/` and `output/` in the repository where you use it, and add the following to `.gitignore` so decks are never committed by accident:

```text
.pptx-review-tmp/
input/*
!input/.gitkeep
output/*
!output/.gitkeep
```

To try it out, generate a sample deck packed with AI-looking elements:

```sh
python .claude/skills/pptx-review/scripts/make_sample.py input/sample.pptx
```

## License

[MIT](LICENSE)
