#!/usr/bin/env bash
# Symlink all skills into common agent skill directories.
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Auto-discover skill dirs (folders containing SKILL.md)
mapfile -t SKILLS < <(
  find "$SRC" -mindepth 2 -maxdepth 2 -type f -name 'SKILL.md' -printf '%h\n' \
    | xargs -I{} basename {} \
    | sort
)

if [[ ${#SKILLS[@]} -eq 0 ]]; then
  echo "No skills found under $SRC" >&2
  exit 1
fi

link_into() {
  local dest_root="$1"
  local label="$2"
  mkdir -p "$dest_root"
  echo "→ $label ($dest_root)"
  for s in "${SKILLS[@]}"; do
    local target="$dest_root/$s"
    if [[ -L "$target" && "$(readlink -f "$target")" == "$SRC/$s" ]]; then
      echo "  verified $s"
      continue
    fi
    if [[ -e "$target" && ! -L "$target" ]]; then
      echo "  skip $s — real directory already exists (not overwriting)"
      continue
    fi
    ln -sfn "$SRC/$s" "$target"
    echo "  linked $s"
  done
}

verify_links() {
  local dest_root="$1"
  local label="$2"
  local failures=0

  for s in "${SKILLS[@]}"; do
    local target="$dest_root/$s"
    if [[ ! -L "$target" || "$(readlink -f "$target")" != "$SRC/$s" ]]; then
      echo "  ERROR: $label cannot load $s from $SRC/$s" >&2
      failures=1
    fi
  done

  return "$failures"
}

echo "Source: $SRC"
echo "Skills (${#SKILLS[@]}): ${SKILLS[*]}"
echo

CODEX_SKILLS_DIR="${CODEX_HOME:-$HOME/.codex}/skills"
mkdir -p "$CODEX_SKILLS_DIR"
link_into "$CODEX_SKILLS_DIR" "Codex"
verify_links "$CODEX_SKILLS_DIR" "Codex"

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
echo "Done. Verified all ${#SKILLS[@]} Codex skill links. Reload the agent if skills don't appear immediately."
