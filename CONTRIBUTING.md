# Contributing

Thanks for helping make Agent Skills more useful, reliable, and portable.

## Principles

- Add knowledge a capable agent would not reliably infer on its own.
- Prefer concise operating guidance over broad tutorials.
- Put triggering language in frontmatter and execution guidance in the body.
- Preserve user data and make destructive boundaries explicit.
- Verify generated artifacts, commands, and reusable scripts.
- Keep provider- or framework-specific depth in `references/` when practical.

## Skill structure

```text
skill-name/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/        # optional
└── scripts/           # optional stdlib helpers
```

Call helpers as `python scripts/<name>.py` from the skill directory (that is how
`install.sh` exposes them). Do not use repo-root paths like `python docx/scripts/…`.
If the same helper must ship with more than one skill, copy it — skills install
independently.

Folder names and frontmatter `name` values must use lowercase kebab-case and match exactly.

```yaml
---
name: skill-name
description: >-
  What the skill does and the requests that should trigger it.
---
```

Keep the frontmatter limited to `name` and `description`. Keep the core `SKILL.md` under 500 lines;
move detailed recipes, schemas, and variant-specific guidance into directly linked references.

## Quality checklist

- [ ] Trigger description identifies both capability and usage context.
- [ ] Scope boundaries identify neighboring skills and exclusions.
- [ ] Instructions use direct, imperative language.
- [ ] Risky actions require appropriate authorization and exact targets.
- [ ] Existing files and user changes are preserved by default.
- [ ] Commands avoid secrets, brittle substitutions, and unnecessary interactivity.
- [ ] Examples are syntactically valid and tested when dependency-sensitive.
- [ ] `python scripts/validate_skills.py` and `python scripts/forward_test.py` pass after changes to helpers or high-risk skills.
- [ ] Local Markdown references resolve.
- [ ] `agents/openai.yaml` still matches the skill's intent.
- [ ] `bash -n install.sh` and `git diff --check` pass.

`install.sh` is POSIX-portable bash 3.2 (macOS `/bin/bash`): no `mapfile`, GNU
`find -printf`, or `readlink -f`. It skips real directories and any existing
symlink that does not already point at this checkout, so a bundled Grok skill
of the same name is not clobbered. `scripts/validate_skills.py` hash-compares
the four `soffice.py` copies, greps skill markdown for known-bad example
tokens, and `ast.parse`s python fences (skipping oversized blocks). `agents/openai.yaml`
is a key presence check, not a PyYAML parse — PyYAML is not in the stdlib.

## Pull requests

Keep changes focused. Explain the behavior the skill improves, the failure mode it prevents, and how
you validated the revision. For high-risk skills—Git, SQL, PDF forms, presentations, and macro-enabled
workbooks—include a realistic forward-test scenario when possible.

GitHub Actions pins use major tags (`actions/checkout@v4`, `actions/setup-python@v5`). Pinning
each action to a full commit SHA is optional.
