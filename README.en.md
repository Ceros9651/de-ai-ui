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
.mcp.json                            Example Playwright MCP config
```

## Design decisions

- Subagents cannot ask the user questions, so analysis (`ui-reviewer`) and consultation (AskUserQuestion in the main conversation) are separated.
- At most 5 issues per review. The rest are summarized and can be left for the next review.
- Only real, shipping apps are used as references — no template marketplaces, concept shots, or AI-generated showcases.
- The screenshot browser runs with `--isolated` and never touches the user's own data. For screens that would otherwise be empty, describe how to load test data under "データの準備" (data preparation) in `project.md`.
- `/ui-review` runs only when you invoke it explicitly (`disable-model-invocation: true`).

## License

[MIT](LICENSE)
