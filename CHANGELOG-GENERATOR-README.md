# Structured Changelog Generator

This solution is for bounty #1. It provides both accepted entry points:

- `bash changelog.sh`
- Claude Code skill `/generate-changelog` via `.claude/skills/generate-changelog/SKILL.md`

## Setup In 3 Steps

1. Copy `changelog.sh` and `.claude/skills/generate-changelog/SKILL.md` into a git repository.
2. Run `bash changelog.sh` from the repository root.
3. Commit the generated `CHANGELOG.md`.

## Behavior

The script finds the most recent reachable tag:

```bash
git describe --tags --abbrev=0
```

Then it reads commits in `<last-tag>..HEAD`, skips merge commits, and categorizes each commit into:

- `Added`
- `Fixed`
- `Changed`
- `Removed`

If a repository has no tags, the script explicitly notes that and generates a changelog from all commits.

## Categorization Rules

- `Added`: `feat:`, `feature:`, `add:`, `create:`, `implement:`, or similar add/implement wording.
- `Fixed`: `fix:`, `bug:`, `patch:`, `repair:`, or similar fix wording.
- `Removed`: `remove:`, `delete:`, `drop:`, `deprecate:`, or similar removal wording.
- `Changed`: all other commits, including docs, chores, refactors, dependency updates, and uncategorized changes.

## Test Command

```bash
bash changelog.sh SAMPLE-CHANGELOG.md
```

`SAMPLE-CHANGELOG.md` in this PR was generated from a real public GitHub repository.
