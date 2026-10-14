---
name: generate-changelog
description: Use when generating or updating a project's CHANGELOG.md from git history since the last tag — categorizing commits into Added/Fixed/Changed/Removed, replacing the living Unreleased section on re-run.
---

# Generate Changelog

Produce a properly formatted `CHANGELOG.md` from a repository's git history.

## When to use

- The user asks for a changelog, release notes, or "what changed since the last release"
- Before cutting a release or writing release notes
- When a repo has no CHANGELOG.md and the user wants one bootstrapped

## How

Run the bundled script against the target repository:

```bash
bash generate-changelog/changelog.sh /path/to/repo
```

Behavior:

- Finds the range since the last git tag (`git describe --tags --abbrev=0`); falls back to full history when the repo has no tags
- Skips merge commits and version-bump noise
- Categorizes each commit: conventional-commit types (`feat` → Added, `fix` → Fixed, `refactor`/`perf`/`chore`/`docs`/`test`/`build`/`ci` → Changed, `revert`/`remove` → Removed), with a keyword fallback for non-conventional messages
- Replaces the existing `## Unreleased` section on re-run (idempotent); released sections are never touched
- Each entry carries the short hash, author, and date

## Verify

After running, confirm:

1. `CHANGELOG.md` exists and opens with `# Changelog`
2. Sections appear only when they have entries
3. Re-running does not duplicate the `## Unreleased` section
4. Entries match real commits (`git log <last-tag>..HEAD`)

Override the output path with `CHANGELOG_OUTPUT=NOTES.md bash changelog.sh <repo>`.
