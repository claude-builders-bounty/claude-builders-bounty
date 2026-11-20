# generate-changelog

A Claude Code skill (plus a standalone bash script) that generates a
structured `CHANGELOG.md` section from a project's git history — commits
since the last tag, auto-categorized into **Added / Fixed / Changed /
Removed**.

## Setup (3 steps)

1. Copy this folder into your Claude Code skills directory:
   `cp -r generate-changelog ~/.claude/skills/`
   (or keep it in a repo's `.claude/skills/` for project-local use)
2. `cd` into any git repository.
3. Run `/generate-changelog` in Claude Code — or use the script directly:
   `bash changelog.sh`

## Requirements

- `git` and `bash` (no other dependencies, no network access needed)

## Example

Given this history after tag `v1.0.0`:

```
feat: add user profile page
fix(auth): stop token refresh loop
refactor!: drop support for Node 12
chore: remove legacy XML exporter
```

`bash changelog.sh` prepends:

```markdown
## [Unreleased] - 2026-11-20

### Added

- Add user profile page

### Fixed

- Stop token refresh loop

### Changed

- **Breaking:** Drop support for Node 12

### Removed

- Remove legacy XML exporter
```

See `examples/sample-output.md` for a full generated `CHANGELOG.md` from a
real test run.

## Options

| Flag             | Meaning                                  | Default       |
| ---------------- | ---------------------------------------- | ------------- |
| `--output FILE`  | Changelog file to update                 | `CHANGELOG.md` |
| `--since TAG`    | Start tag (default: latest tag)          | latest tag    |
| `--version NAME` | Version heading (default: `Unreleased`, or the tag when HEAD is on it) | — |
| `--date DATE`    | Section date (`YYYY-MM-DD`)              | today         |
