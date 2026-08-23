#!/usr/bin/env bash
# Symlink all skills into common agent skill directories.
# Portable to bash 3.2 (macOS): no mapfile, find -printf, or readlink -f.
# Never clobber a real directory or a symlink that points somewhere else
# (Grok and other agents may already ship a skill with the same name).
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

resolve_path() {
  python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$1"
}

SRC="$(resolve_path "$SRC")"

SKILLS=()
for skill_file in "$SRC"/*/SKILL.md; do
  [ -f "$skill_file" ] || continue
  SKILLS+=("$(basename "$(dirname "$skill_file")")")
done

if [ ${#SKILLS[@]} -gt 0 ]; then
  _sorted="$(printf '%s\n' "${SKILLS[@]}" | LC_ALL=C sort)"
  SKILLS=()
  while IFS= read -r _s; do
    [ -n "$_s" ] || continue
    SKILLS+=("$_s")
  done <<EOF
$_sorted
EOF
fi

if [ ${#SKILLS[@]} -eq 0 ]; then
  echo "No skills found under $SRC" >&2
  exit 1
fi

LINKED=0

link_into() {
  local dest_root="$1"
  local label="$2"
  local target resolved
  mkdir -p "$dest_root"
  echo "→ $label ($dest_root)"
  for s in "${SKILLS[@]}"; do
    target="$dest_root/$s"
    if [ -L "$target" ]; then
      resolved="$(resolve_path "$target")"
      if [ "$resolved" = "$SRC/$s" ]; then
        echo "  verified $s"
        LINKED=$((LINKED + 1))
        continue
      fi
      echo "  skip $s — existing symlink points elsewhere ($resolved); not clobbering" >&2
      continue
    fi
    if [ -e "$target" ]; then
      echo "  skip $s — real path already exists (not overwriting)" >&2
      continue
    fi
    ln -s "$SRC/$s" "$target"
    echo "  linked $s"
    LINKED=$((LINKED + 1))
  done
}

echo "Source: $SRC"
echo "Skills (${#SKILLS[@]}): ${SKILLS[*]}"
echo

CODEX_SKILLS_DIR="${CODEX_HOME:-$HOME/.codex}/skills"
mkdir -p "$CODEX_SKILLS_DIR"
link_into "$CODEX_SKILLS_DIR" "Codex"

if mkdir -p "${GROK_HOME:-$HOME/.grok}/skills" 2>/dev/null; then
  link_into "${GROK_HOME:-$HOME/.grok}/skills" "Grok"
fi

if mkdir -p "$HOME/.claude/skills" 2>/dev/null; then
  link_into "$HOME/.claude/skills" "Claude Code"
fi

if mkdir -p "$HOME/.cursor/skills" 2>/dev/null; then
  link_into "$HOME/.cursor/skills" "Cursor"
fi

echo
if [ "$LINKED" -eq 0 ]; then
  echo "No skills were linked anywhere." >&2
  exit 1
fi
echo "Done. Linked or verified $LINKED skill path(s). Reload the agent if skills don't appear immediately."
