---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the last tag. Use when the user asks for a changelog, release notes, or runs /generate-changelog.
---

# Generate Changelog

## When to use

User wants a `CHANGELOG.md` from recent commits, release notes, or invokes `/generate-changelog`.

## How to run

From the git repository root:

```bash
bash "${CLAUDE_SKILL_DIR:-.}/changelog.sh" CHANGELOG.md
```

Or absolute path if installed under skills:

```bash
bash ~/.claude/skills/generate-changelog/changelog.sh CHANGELOG.md
```

## Behavior

1. Finds the latest git tag (`git describe --tags --abbrev=0`).
2. Lists commits since that tag (or all commits if no tags).
3. Categorizes subjects into **Added / Fixed / Changed / Removed**.
4. Writes a dated section to `CHANGELOG.md`.

## Categories (heuristic)

| Bucket | Commit subject signals |
|--------|------------------------|
| Added | `feat`, `add`, `create`, `implement`, `support` |
| Fixed | `fix`, `bug`, `hotfix`, `patch`, `resolve` |
| Changed | `chore`, `refactor`, `perf`, `update`, `docs`, `ci`, conventional non-feat/fix |
| Removed | `remove`, `delete`, `drop`, `deprecate` |

Unmatched subjects fall into **Changed**.

## Output shape

```markdown
# Changelog

## YYYY-MM-DD

_Changes since `vX.Y.Z`_

### Added
- ...

### Fixed
- ...

### Changed
- ...

### Removed
- ...
```
