# Agent Skills

Portable **Agent Skills** (open `SKILL.md` standard) for Grok, Codex, Claude Code, Cursor, and anything else that loads `name/SKILL.md` folders.

## Document & content

| Skill | Use for |
|-------|---------|
| **docx** | Word — create, templates, tracked changes, visual QA |
| **pptx** | PowerPoint — PptxGenJS, design system, charts, visual QA |
| **xlsx** | Excel — openpyxl, formulas, formatting, charts |
| **pdf** | PDF — extract, merge, reportlab, OCR, forms |
| **csv** | CSV/TSV clean, validate, merge → handoff to analysis |
| **markdown** | READMEs, ADRs, changelogs, docs sites |
| **email-html** | Transactional/newsletter HTML + plain text |
| **diagrams** | Mermaid / PlantUML / D2 / ASCII architecture diagrams |
| **ics** | Calendar invites (.ics), RRULE, timezones |

## Data & analysis

| Skill | Use for |
|-------|---------|
| **data-analysis** | EDA, metric definitions, charts, gotchas, A/B readouts |
| **sql** | Queries, indexes, EXPLAIN, migrations (Postgres-first) |
| **json-yaml** | JSON/YAML/TOML, JSON Schema, config merges |

## Engineering

| Skill | Use for |
|-------|---------|
| **git-pr** | Commits, branches, PR descriptions, rebase hygiene |
| **api** | REST design, OpenAPI, errors, pagination, webhooks |
| **testing** | pytest / Jest / Go tests, fakes, flaky kill list |
| **docker** | Dockerfiles, multi-stage, Compose, image hygiene |

## Install

```bash
git clone https://github.com/RobbyBobby77/agent-skills.git
cd agent-skills
bash ./install.sh
```

The installer verifies that every Codex link resolves back to this source
directory and exits with an error if a conflicting real directory prevents a
skill from being installed.

Symlinks into:

- `~/.codex/skills`
- `~/.grok/skills`
- `~/.claude/skills`
- `~/.cursor/skills`

Project-local:

```bash
mkdir -p .agents/skills
skills_root="/path/to/agent-skills"
for s in "$skills_root"/*/SKILL.md; do
  name=$(basename "$(dirname "$s")")
  ln -sfn "$(dirname "$s")" ".agents/skills/$name"
done
```

## Common dependencies

Install dependencies in a project virtual environment or tool-specific environment when possible;
do not install the entire list merely to make skill metadata discoverable.

```bash
# Node
npm install -g docx pptxgenjs mjml

# Python
pip install openpyxl xlsxwriter pandas polars pypdf pdfplumber reportlab \
  "markitdown[all]" pdf2image pytesseract python-pptx pyyaml jsonschema \
  icalendar matplotlib seaborn plotly

# System (as needed)
# pandoc libreoffice poppler-utils qpdf tesseract-ocr docker
```

## Layout

```
agent-skills/
├── README.md
├── install.sh          # auto-discovers */SKILL.md
├── docx/ pptx/ xlsx/ pdf/ csv/ markdown/ email-html/ diagrams/ ics/
├── data-analysis/ sql/ json-yaml/
└── git-pr/ api/ testing/ docker/
```

Each skill: `SKILL.md` + optional `references/` (progressive disclosure).

## Standard

Frontmatter is only:

```yaml
---
name: skill-name
description: >-
  What it does + when to trigger. Keywords matter.
---
```

Compatible with [agentskills.io](https://agentskills.io) style loaders.
