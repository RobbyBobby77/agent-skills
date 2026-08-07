---
name: markdown
description: >
  Write and structure high-quality Markdown: READMEs, docs, ADRs, changelogs,
  RFCs, wikis, GitHub/GitLab flavored markdown, tables, diagrams-in-docs, and
  doc site pages (Docusaurus/MkDocs/VitePress). Use when the deliverable is .md
  or documentation content. Do not use for Word/PDF deliverables (convert later
  if needed).
---

# Markdown

## Workflow

1. Inspect nearby documentation, repository instructions, and the target renderer before editing.
2. Match the existing voice, heading hierarchy, link style, wrapping, and code-block conventions.
3. Keep commands executable from the stated working directory and distinguish placeholders from literal values.
4. Validate internal links, anchors, code fences, and renderer-specific syntax.
5. Review the rendered structure and avoid unrelated reflow.

## Defaults

- **GFM** (GitHub Flavored Markdown): tables, task lists, strikethrough, footnotes where supported
- One H1 per page (`# Title`)
- ATX headings (`##`) not Setext underlines
- Fenced code blocks with language tags
- Relative links for in-repo paths
- Wrap prose ~100–120 chars optional; never break code fences or tables for wrapping

---

## Document types

### README (repo root)

```markdown
# Project Name

One-sentence pitch.

## Features
- …

## Quick start

Fenced bash block with install + run commands.

## Configuration

Table: Var | Default | Description

## Usage
## Development
## License
```

### ADR (Architecture Decision Record)

```markdown
# ADR-0001: Title

- Status: Proposed | Accepted | Superseded by ADR-000X
- Date: YYYY-MM-DD

## Context
## Decision
## Consequences
### Positive
### Negative
### Neutral
```

### Changelog (Keep a Changelog)

```markdown
# Changelog

## [Unreleased]
### Added
### Changed
### Fixed

## [1.2.0] - 2026-03-01
### Added
- Feature X (#123)
```

### RFC / design doc skeleton

Problem → Goals / non-goals → Proposal → Alternatives → Risks → Rollout → Open questions

---

## Style rules

1. **Lead with the point** — first paragraph answers "what is this / why care"
2. **Scannable** — short sections, bullets for lists of 3+, tables for comparisons
3. **Runnable examples** — copy-paste commands that work from repo root
4. **No orphan headings** — every heading has content
5. **Link to code** with line-stable paths (`src/foo.ts`) not `click here`
6. **Images** — alt text required: `![Alt](docs/img/arch.png)`
7. **Version-sensitive info** — pin versions or say "as of DATE"
8. **Avoid** giant walls of generated API dumps — link out or collapse

### Tables

```markdown
| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--port` | int | `8080` | Listen port |
```

Align pipes; keep cells short; put long prose below the table.

### Code

````markdown
```python
def main() -> None:
    ...
```
````

Call out expected output in a following block or comment when it matters.

### Task lists

```markdown
- [x] Done
- [ ] Todo
```

### Callouts (GFM / GitHub)

```markdown
> [!NOTE]
> Useful context.

> [!WARNING]
> Footgun ahead.

> [!IMPORTANT]
> Must read.
```

---

## Structure for long docs

```
docs/
  index.md          # overview + navigation
  getting-started.md
  concepts/
  guides/
  reference/
  adr/
```

Cross-link liberally. Prefer deep links over duplicating content.

---

## Lint mindset

- Broken relative links
- Heading hierarchy skips (`##` → `####`)
- Code blocks missing language
- Trailing whitespace / tabs mixed
- Secrets or internal hostnames accidentally pasted

```bash
# if available
markdownlint '**/*.md'
lychee README.md docs/
```

---

## Convert when needed

```bash
pandoc README.md -o README.pdf
pandoc doc.md -o doc.docx
```

Keep Markdown as source of truth for engineering docs.
