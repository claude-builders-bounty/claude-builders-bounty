---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the last tag. Use when the user runs /generate-changelog, asks for a changelog, release notes, or wants commits categorized into Added/Fixed/Changed/Removed.
---

# Generate Changelog

Produce a Keep-a-Changelog-style `CHANGELOG.md` from git commits since the latest tag.

## When to use

- User runs `/generate-changelog`
- User asks for release notes or a changelog update
- Preparing a version bump or GitHub release

## Steps

1. Confirm the target repo path (default: current working directory).
2. Run the generator:

```bash
bash submissions/bounty-1-changelog/scripts/changelog.sh CHANGELOG.md .
```

Or from a global install:

```bash
bash ~/.claude/skills/generate-changelog/scripts/changelog.sh
```

3. Read the generated file and offer to commit it if the user wants.
4. If the output looks sparse, mention that no tag exists yet (script includes all history).

## Categorization rules

| Bucket | Conventional commit prefixes | Heuristics |
|--------|------------------------------|------------|
| Added | `feat`, `feature`, `add` | "implement", "introduce", "support" |
| Fixed | `fix`, `bugfix`, `hotfix` | "bug", "patch", "resolve" |
| Changed | `refactor`, `chore`, `perf`, `docs`, `ci` | default bucket |
| Removed | `remove`, `delete`, `drop` | destructive verbs in subject |

## Output format

```markdown
## [YYYY.MM.DD] - YYYY-MM-DD

Changes since v1.2.3

### Added
- feat(auth): add OAuth callback (a1b2c3d, 2026-06-10)

### Fixed
...
```

## Quality checks

- Ensure merge commits are excluded (script uses `--no-merges`).
- Verify at least one section is populated before committing.
- Preserve existing changelog history manually if the project already maintains one — append rather than overwrite when asked.