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
└── references/        # optional
```

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
- [ ] Local Markdown references resolve.
- [ ] `agents/openai.yaml` still matches the skill's intent.
- [ ] `bash -n install.sh` and `git diff --check` pass.

## Pull requests

Keep changes focused. Explain the behavior the skill improves, the failure mode it prevents, and how
you validated the revision. For high-risk skills—Git, SQL, PDF forms, presentations, and macro-enabled
workbooks—include a realistic forward-test scenario when possible.
