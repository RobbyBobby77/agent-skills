---
name: git-pr
description: >
  Prepare and execute safe Git workflows: inspect repository state, stage and
  commit scoped changes, create branches, synchronize history, resolve conflicts,
  and package pull/merge requests. Use when the user asks to commit, push, open or
  describe a PR/MR, split commits, rebase, clean history, or check readiness to
  ship. Keep remote publishing provider-neutral; defer GitHub-specific publishing
  to a dedicated GitHub workflow when one is available. Do not use for generic
  code review unless the task is PR packaging.
---

# Git & Pull Requests

## Operating rules

- **Never** force-push `main`/`master`/`trunk`
- **Never** change git user config unless asked
- Do not commit, amend, rebase, push, or open a PR/MR unless the user's request authorizes that action
- Preserve unrelated staged, unstaged, and untracked work; never stash it automatically
- Do not stage secrets (`.env`, private keys, tokens, credentials) or generated artifacts without intent
- Use non-interactive commands. Avoid editor prompts, `git add -p`, and brittle shell substitutions
- Prefer reversible operations and explicit paths. Treat checkout/restore, reset, clean, and force-push as destructive
- Follow repository instructions in `AGENTS.md`, `CONTRIBUTING.md`, or equivalent before changing history

---

## Inspect before changing state

```bash
git status --short --branch
git rev-parse --show-toplevel
git rev-parse --abbrev-ref HEAD
git branch -vv
git remote -v
git diff --stat
git diff --staged
git log --oneline --decorate -15
```

Inspect the full unstaged diff when it is relevant. Determine:

- current branch and whether it is protected
- upstream and ahead/behind state
- pre-existing staged changes and unrelated work
- repository-specific checks and commit conventions
- the exact files/hunks authorized for the requested operation

---

## Commits

### Stage intentionally

Use explicit paths and verify the index:

```bash
git add -- path/to/file another/file
git diff --cached --stat
git diff --cached
git diff --cached --check
```

Do not use `git add .` or `git add -A` when unrelated work exists. If requested changes and
user changes overlap in one file, avoid staging the user's hunks; ask only when the scope cannot
be separated safely with non-interactive tooling.

When unrelated changes are already staged, `git commit --only -- <authorized-paths>` can commit
the selected working-tree paths without consuming the existing index. Inspect those complete paths
first; it is unsafe when authorized and unrelated edits share a file.

### Message format

```
Imperative summary ≤72 chars

Optional body: why (not what). Wrap ~72.
Reference issues: Fixes #123
```

Examples:
- `fix auth: refresh tokens before expiry`
- `feat(api): add bulk export endpoint`
- `docs: document rate limit headers`

### What makes a good commit

- One logical change
- Builds/tests pass at the commit if feasible
- No "WIP" / "fix stuff" on shared history

```bash
git commit -m "feat(checkout): reject expired discount codes" \
  -m "Prevents double-spend on codes past ends_at."
```

After committing, verify `git show --stat --oneline HEAD` and `git status --short --branch`.

### Amend only when

- the commit is confirmed local and belongs to the current task, or
- the user explicitly requests rewriting a pushed personal branch and accepts a force-with-lease push

```bash
git commit --amend --no-edit
```

Do not amend merely to hide an additional logical change; create a separate commit when appropriate.

---

## Branches

```bash
git fetch origin
git switch -c feat/short-name origin/main
```

Use the repository's base branch and naming convention; do not assume `origin/main` exists.
Common names: `feat/…`, `fix/…`, `chore/…`, `docs/…` — short, kebab-case.

---

## Synchronize history

Fetch first and inspect divergence:

```bash
git fetch origin
git status --short --branch
git rev-list --left-right --count '@{upstream}...HEAD'
```

Use the repository/team strategy. Rebase only a personal feature branch that others do not depend
on; otherwise merge the base branch. Resolve conflicts by intent, run affected tests, and inspect
the resulting history before any push.

Rebase requires a clean worktree. If unrelated user changes remain, do not use `--autostash` and do
not create a stash without permission. Stop and ask whether to preserve them in a named stash or use
another isolation strategy; record the exact stash identity and restore with `apply --index` before
dropping it.

If a rewritten pushed branch must be updated, use `git push --force-with-lease` only after verifying
the remote branch and user authorization. A lease failure is new remote work: stop and inspect it.

---

## Pull and merge requests

Prepare locally before publishing:

1. Confirm the remote/provider, base branch, current branch, and authentication.
2. Check whether a PR/MR already exists for the branch.
3. Review the complete base-to-head diff and commit list.
4. Run the relevant tests or clearly state what could not be run.
5. Push and create/update the PR/MR only when requested.

When a dedicated provider integration is available, use it for remote metadata and publishing;
keep this skill focused on safe local Git state and provider-neutral packaging.

### Create (GitHub CLI)

```bash
gh auth status
gh pr view --json number,url,state,title
git push -u origin HEAD
gh pr create --draft \
  --title "feat(checkout): reject expired discount codes" \
  --body-file /path/to/temporary/pr-body.md
```

Create the body file in a unique temporary directory with the available safe file-editing mechanism. Default to a draft unless the
user says the work is ready or repository policy clearly specifies otherwise.

### PR description template

```markdown
## Summary
- Bullet outcomes (user/system impact), not file lists

## Changes
- Optional deeper detail

## Test plan
- [ ] Concrete verification steps

## Risk / rollout
- Low/med/high; feature flag? migration?
```

### Size

- Prefer <400 lines changed when possible; split by layer (schema → API → UI) if huge
- Stack/depend PRs when tooling supports it

---

## Conflicts

1. Open conflicted files; find `<<<<<<<`
2. Keep correct intent (not blindly "theirs/ours")
3. `git add` resolved files
4. `git rebase --continue` or `git merge --continue`
5. Run tests

Before starting, record whether a merge, rebase, or cherry-pick is active. Abort only the operation
started for the current task; do not abort a pre-existing user operation.

---

## Read-only diagnostics

```bash
git log --oneline --graph --decorate -20
git show --stat HEAD
git blame path/to/file
git diff --name-status base...HEAD
git diff --check base...HEAD
```

## Destructive boundaries

- Unstaging with `git restore --staged -- path` is normally recoverable, but verify the target first
- Discarding work with `git restore --worktree`, resetting, cleaning, deleting branches, or dropping stashes requires explicit intent and exact targets
- Never use plain `--force`; never bypass hooks unless explicitly requested and justified
- Never rewrite remote-tracking refs to conceal divergence
- Never commit `node_modules`, build artifacts, or personal IDE files unless the repository intentionally tracks them
