---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the latest tag. Use when the user asks for a changelog, release notes from commits, or /generate-changelog.
---

# Generate CHANGELOG

## When to use

- User asks for `CHANGELOG.md`, release notes, or "what changed since last tag"
- Before tagging a release

## Steps

1. Ensure you are at the repository root (directory with `.git`).
2. Run:

```bash
bash scripts/changelog.sh
# optional: bash scripts/changelog.sh -o docs/RELEASE-NOTES.md
```

3. Read `CHANGELOG.md` (or `-o` path). Edit wording if needed; do not drop security items.

## Behavior

- Range: `latest-tag..HEAD`, or all commits if no tags exist
- Groups: **Added**, **Fixed**, **Changed**, **Removed**, **Security**, **Other**
- Conventional commits: `feat` → Added, `fix` → Fixed, `chore|refactor|perf|ci|build|style` → Changed, `remove|revert` → Removed, `security` → Security

## Verify

```bash
test -s CHANGELOG.md && head -20 CHANGELOG.md
```
