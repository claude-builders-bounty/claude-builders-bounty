# Generate Changelog

Generate a structured `CHANGELOG.md` from git history.

## Setup

1. Copy or keep this folder in the target repository.
2. Run `chmod +x changelog.sh generate-changelog/changelog.sh`.
3. Run `bash changelog.sh`.

The script finds the latest reachable git tag, collects commits since that tag,
and writes a Keep-a-Changelog-style file with `Added`, `Fixed`, `Changed`, and
`Removed` sections.

## Usage

```bash
bash changelog.sh
bash changelog.sh --output docs/CHANGELOG.md
bash changelog.sh --from v1.2.0 --to HEAD
```

## Claude Code command

This contribution also includes `.claude/commands/generate-changelog.md`, so a
Claude Code user can run `/generate-changelog` from the repository and have the
assistant execute the same `bash changelog.sh` workflow.

## Categorization

| Section | Commit prefixes |
| --- | --- |
| Added | `feat:`, `add:`, `create:`, `implement:` |
| Fixed | `fix:`, `bugfix:`, `hotfix:`, `repair:`, `resolve:` |
| Changed | `change:`, `refactor:`, `docs:`, `chore:`, `perf:`, `test:`, `build:`, `ci:`, `style:`, `update:`, `improve:` |
| Removed | `remove:`, `delete:`, `drop:`, `deprecate:` |

Commits without a recognized prefix are kept under `Changed`.

## Test

```bash
bash generate-changelog/test_changelog.sh
```
