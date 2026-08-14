---
name: markdown
description: >
  Edit and write repository documentation so it matches the existing voice and
  actually renders: READMEs, ADRs, changelogs, RFCs, wikis, and doc-site pages.
  Use when the deliverable is .md/.mdx or the user asks to fix docs, links,
  anchors, or renderer-specific syntax. Prefer diagrams for figure source,
  json-yaml for config frontmatter-only edits, and docx/pdf when the output is
  not Markdown. Do not use for casual chat replies or code comments.
---

# Markdown

Agents already know GFM. This skill exists because they rewrite the wrong file,
break the renderer, invent a second voice, and ship commands that do not run.

## Related skills

| Need | Skill |
|------|-------|
| Architecture / sequence figures | `diagrams` |
| Commit or PR description packaging | `git-pr` |
| Strict YAML/JSON frontmatter or config | `json-yaml` |
| Word / PDF / slides as the deliverable | `docx` / `pdf` / `pptx` |

## Workflow

1. **Inspect** the nearest docs, `CONTRIBUTING`/`AGENTS`, doc-site config, and the target renderer before writing.
2. **Match** heading depth, link style, wrapping, callout syntax, and tone. Do not restyle the rest of the page.
3. **Change the smallest surface** that answers the request. Do not rebuild a README to add one section.
4. **Keep commands executable** from the stated working directory. Mark placeholders so they cannot be pasted as literals.
5. **Verify** relative links, heading anchors, fences, and renderer-specific syntax. Report what you could not render.

**Hard rules**
- The repo's existing docs are the style guide. Nearby files beat this skill.
- Never invent badges, install methods, features, or versions you did not inspect.
- Never reflow unrelated prose, tables, or code fences to "clean up" wrapping.
- Never use this skill's templates when a file of that type already exists — edit it.
- If the renderer is unknown, write conservative GFM and say so.

---

## Identify the renderer

| Signal | Renderer | Consequence |
|--------|----------|-------------|
| GitHub repo / PR / wiki | GFM + GitHub slugs | `[!NOTE]` callouts OK; relative links from the file |
| GitLab repo / wiki | GFM + GitLab slugs | Different anchor algorithm; `[[_TOC_]]` is GitLab-only |
| `mkdocs.yml` | MkDocs / Material | Admonitions are `!!! note`; nav is config, not a guess |
| `docusaurus.config.*` | Docusaurus / MDX | JSX and `{` in prose break pages; import diagrams as MDX |
| `vitepress` / `.vitepress/` | VitePress | Vue containers; frontmatter drives sidebar |
| Slack / email paste | Almost-GFM | No relative repo links; no HTML |

Doc-site frontmatter, admonitions, and slug rules: [references/renderers.md](references/renderers.md).

---

## Edit, don't replace

Before adding a section, search for the same topic. Duplicate "Getting started" pages are how docs rot.

```text
Allowed: add a subsection, fix a command, retarget a link, draft a missing ADR
Not allowed without being asked: rewrite the README, restyle every heading, convert
Setext to ATX across the tree, "standardize" someone else's docs
```

Preserve:

- Existing heading IDs (`{#custom-id}`) and published URLs
- Image paths and alt text unless they are wrong
- Generated fragments (`<!-- prettier-ignore -->`, autogen markers)

---

## Commands and placeholders

State the working directory above the fence. Distinguish copy-paste literals from values the user must substitute:

````markdown
From the repo root:

```bash
npm test -- workspace-web
```

Replace `<cluster-id>` (including the angle brackets) before running:

```bash
kubectl get pods -n <cluster-id>
```
````

- Pin versions or write "as of YYYY-MM-DD"
- Do not wrap tables or fences to satisfy a prose column width
- Language-tag every fence; untagged fences break most highlighters and some MDX pipelines

---

## Links and anchors

Resolve links **from the file you are editing**, not from the repo root.

| Link | Resolves from `docs/guide/install.md` |
|------|----------------------------------------|
| `[config](../reference/config.md)` | `docs/reference/config.md` |
| `[config](docs/reference/config.md)` | **broken** (looks for `docs/guide/docs/...`) |
| `[code](../../src/cli.ts)` | OK if that path exists |

- Prefer path links over `#` anchors when the heading text is likely to change
- When you must anchor, compute the slug for **this** renderer — GitHub and GitLab disagree (see [references/renderers.md](references/renderers.md))
- After a heading rename, grep for the old slug before shipping
- Images need alt text: `![Checkout sequence](../img/checkout.png)`
- Do not paste internal hostnames, tokens, or customer data into examples

```bash
# existence check for relative targets cited from FILE (argv after "-")
python - README.md <<'PY'
from pathlib import Path
import re, sys
src = Path(sys.argv[1])
text = src.read_text()
for link in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
    target = link.split()[0].split("#", 1)[0]
    if not target or target.startswith(("http://", "https://", "mailto:")):
        continue
    dest = (src.parent / target).resolve()
    print(("OK " if dest.is_file() else "MISSING "), target)
PY
```

---

## When to write which document

Do not start from a skeleton if the repo already has one.

| Situation | Document |
|-----------|----------|
| How to run / configure this repo | README or `docs/getting-started.md` |
| A decision we must not relitigate | ADR in the repo's existing ADR format |
| User-visible change in a released product | Changelog entry in the repo's existing changelog |
| Cross-team proposal with alternatives | RFC / design doc, linked from the README |
| Reference that will grow | A focused page under `docs/`, not a longer README |

Lead with the point in the first paragraph. One H1 per page. ATX headings (`##`). No orphan headings. No heading-level skips.

If you need a starter only because the file does not exist:

```markdown
# <thing>

<one sentence: what it is and why it exists>

## Use this when
## Do not use this when
```

Everything else — Features, Quick start, ADR status lines, Keep a Changelog headings — copy from a sibling file in *this* repo.

---

## QA

1. Open the diff. Confirm you did not rewrite unrelated sections.
2. Click or resolve every new/changed relative link.
3. Confirm heading hierarchy and that new anchors are not collisions.
4. Grep the page for leftover `TODO`, `TBD`, `lorem`, `XXXX`, and fake URLs.
5. If a doc site is present, name the renderer and any syntax you could not compile.

```bash
# if the repo already uses them
markdownlint README.md docs/
lychee README.md docs/
```
