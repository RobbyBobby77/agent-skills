#!/usr/bin/env python3
"""Structural checks from CONTRIBUTING.md: frontmatter, names, links, openai.yaml.

Behavioral helper checks live in scripts/forward_test.py.

No third-party dependencies: frontmatter here is deliberately restricted to
two scalar/folded-block keys (name, description), so a small hand parser is
more honest than pulling in pyyaml for two fields.
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAX_SKILL_LINES = 500
KEBAB_CASE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
LINK_PATTERN = re.compile(r"\]\(([^)]+)\)")
CODE_SPAN = re.compile(r"`[^`\n]*`")
FENCED_BLOCK = re.compile(r"```.*?```", re.S)
# Tokens that previously shipped as copy-pasteable landmines. Keep them out of
# skill markdown so the original bugs cannot silently return.
KNOWN_BAD_TOKENS = (
    "left_content",
    "vitest run --repeat",
    "pytest --count",
)


def strip_code(text: str) -> str:
    """Drop fenced blocks and inline code spans so illustrative syntax
    (e.g. a code example showing `![Alt](docs/img/arch.png)`) isn't mistaken
    for a real navigational link."""
    return CODE_SPAN.sub("", FENCED_BLOCK.sub("", text))


def find_skill_dirs() -> list[Path]:
    return sorted(
        p.parent for p in ROOT.glob("*/SKILL.md")
    )


def parse_frontmatter(text: str, errors: list[str], label: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        errors.append(f"{label}: SKILL.md must start with a '---' frontmatter block")
        return {}

    end = text.find("\n---", 4)
    if end == -1:
        errors.append(f"{label}: frontmatter block is never closed with '---'")
        return {}

    block = text[4:end]
    fields: dict[str, str] = {}
    current_key = None
    for raw_line in block.splitlines():
        if raw_line and not raw_line[0].isspace():
            match = re.match(r"^([a-zA-Z_]+):\s*(.*)$", raw_line)
            if not match:
                errors.append(f"{label}: unexpected frontmatter line: {raw_line!r}")
                continue
            current_key, value = match.group(1), match.group(2).strip()
            fields[current_key] = "" if value in (">", ">-", "|", "|-") else value
        elif current_key:
            fields[current_key] = (fields[current_key] + " " + raw_line.strip()).strip()

    allowed = {"name", "description"}
    extra = set(fields) - allowed
    if extra:
        errors.append(f"{label}: frontmatter has unexpected keys {sorted(extra)} (only name/description allowed)")

    return fields


def check_openai_yaml(skill_dir: Path, errors: list[str], label: str) -> None:
    path = skill_dir / "agents" / "openai.yaml"
    if not path.is_file():
        errors.append(f"{label}: missing agents/openai.yaml")
        return

    text = path.read_text(encoding="utf-8")
    for key in ("display_name", "short_description", "default_prompt"):
        if f"{key}:" not in text:
            errors.append(f"{label}: agents/openai.yaml is missing '{key}'")


def check_local_links(skill_dir: Path, body: str, errors: list[str], label: str) -> None:
    for target in LINK_PATTERN.findall(strip_code(body)):
        target = target.split(" ", 1)[0].strip()
        if not target or target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        if not (skill_dir / target).is_file():
            errors.append(f"{label}: linked file does not resolve: {target}")


def check_known_bad_tokens(errors: list[str]) -> None:
    paths = sorted(ROOT.glob("*/SKILL.md")) + sorted(ROOT.glob("*/references/*.md"))
    for path in paths:
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(ROOT).as_posix()
        for token in KNOWN_BAD_TOKENS:
            if token in text:
                errors.append(f"{rel}: contains known-bad token {token!r}")


def check_soffice_copies(errors: list[str]) -> None:
    copies = sorted(ROOT.glob("*/scripts/soffice.py"))
    if len(copies) != 4:
        errors.append(f"expected 4 soffice.py copies, found {len(copies)}")
        return
    digests = [(p.relative_to(ROOT).as_posix(), hashlib.sha256(p.read_bytes()).hexdigest()) for p in copies]
    unique = {digest for _, digest in digests}
    if len(unique) != 1:
        listing = ", ".join(f"{path}={digest[:12]}" for path, digest in digests)
        errors.append(f"soffice.py copies are not identical: {listing}")


def validate_skill(skill_dir: Path, errors: list[str]) -> None:
    label = skill_dir.name
    skill_md = skill_dir / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8")
    line_count = text.count("\n") + 1

    if line_count > MAX_SKILL_LINES:
        errors.append(f"{label}: SKILL.md is {line_count} lines (limit {MAX_SKILL_LINES})")

    fields = parse_frontmatter(text, errors, label)

    name = fields.get("name", "")
    if not name:
        errors.append(f"{label}: frontmatter is missing 'name'")
    elif name != label:
        errors.append(f"{label}: frontmatter name '{name}' must match folder name '{label}'")
    elif not KEBAB_CASE.match(name):
        errors.append(f"{label}: frontmatter name '{name}' must be lowercase kebab-case")

    description = fields.get("description", "")
    if len(description) < 20:
        errors.append(f"{label}: description is missing or too short to be a real trigger")

    check_openai_yaml(skill_dir, errors, label)
    check_local_links(skill_dir, text, errors, label)

    references_dir = skill_dir / "references"
    if references_dir.is_dir():
        linked = set(LINK_PATTERN.findall(strip_code(text)))
        for ref_file in references_dir.glob("*.md"):
            rel = f"references/{ref_file.name}"
            if not any(rel in target for target in linked):
                errors.append(f"{label}: references/{ref_file.name} exists but SKILL.md never links to it")


def main() -> int:
    skill_dirs = find_skill_dirs()
    if not skill_dirs:
        print("No SKILL.md files found under", ROOT, file=sys.stderr)
        return 1

    errors: list[str] = []
    check_soffice_copies(errors)
    check_known_bad_tokens(errors)
    for skill_dir in skill_dirs:
        validate_skill(skill_dir, errors)

    if errors:
        print(f"{len(errors)} problem(s) found across {len(skill_dirs)} skills:\n")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(f"All {len(skill_dirs)} skills passed validation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
