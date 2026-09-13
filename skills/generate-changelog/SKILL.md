---
name: generate-changelog
description: Generate a structured CHANGELOG.md from a git repository's commit history since the last tag. Use when the user asks for a changelog, release notes, or "what changed since last release".
---

# Generate Changelog

Create a Keep-a-Changelog style `CHANGELOG.md` from git history.

## Steps

1. Confirm the target is a git repository.
2. Run the generator:

```bash
python3 skills/generate-changelog/changelog_from_git.py --repo . --stdout
```

3. Review the markdown. Write it to `CHANGELOG.md` unless the user asked for stdout only:

```bash
python3 skills/generate-changelog/changelog_from_git.py --repo .
```

## Options

| Flag | Meaning |
|------|---------|
| `--repo PATH` | Repository root (default: cwd) |
| `--output PATH` | Output file (default: `<repo>/CHANGELOG.md`) |
| `--stdout` | Print instead of writing |

## Rules

- Commits after the latest tag are included; no tags means full history.
- Conventional Commits (`feat:`, `fix:`, …) map to Added/Fixed/Changed/Removed.
- Plain `Add …` / `Fix …` / `Remove …` subjects are also mapped.
- Never invent commits; if the range is empty, write an explicit empty section.
