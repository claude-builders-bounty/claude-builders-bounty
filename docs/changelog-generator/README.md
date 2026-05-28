# Changelog Generator

Generate a structured `CHANGELOG.md` from git commits since the latest tag.

## Setup

1. Copy `changelog.sh` into the root of a git repository.
2. Run `bash changelog.sh`.
3. Review and commit the generated `CHANGELOG.md`.

Claude Code users can also run `/generate-changelog` when the `.claude/commands/generate-changelog.md` command is present.

## Categories

- `Added`: `feat`, `feature`, `add`, and similar commit subjects.
- `Fixed`: `fix`, `bugfix`, `repair`, and similar commit subjects.
- `Removed`: `remove`, `delete`, `drop`, and similar commit subjects.
- `Changed`: every other commit subject.

## Options

```bash
bash changelog.sh --repo /path/to/repo --output CHANGELOG.md
```
