---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history when the user asks for /generate-changelog, release notes, or changes since the latest git tag.
---

# Generate Changelog

Use this skill when a user asks Claude Code to create or refresh a `CHANGELOG.md` from Git history.

## Workflow

1. Confirm the current directory is the target Git repository.
2. Run:

   ```bash
   bash changelog.sh
   ```

3. Review `CHANGELOG.md` and adjust any category wording only if a commit subject is ambiguous.

## Options

- Use `--since <ref>` to generate changes from a specific tag or commit.
- Use `--output <path>` to write somewhere other than `CHANGELOG.md`.
- Use `--include-merges` when merge commits should appear in the release notes.

## Output Format

The generated changelog uses this structure:

```markdown
# Changelog

## [Unreleased] - YYYY-MM-DD

_Changes since `v1.2.0`._

### Added

- Add user profile export (abc1234)

### Fixed

- Fix empty-state rendering (def5678)
```
