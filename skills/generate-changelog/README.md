# Generate Changelog

Create a structured `CHANGELOG.md` from git history.

## Setup

1. Copy this repository's `changelog.sh`, `.claude/commands/generate-changelog.md`, and `skills/generate-changelog/` into your project.
2. Run `bash changelog.sh`.
3. Commit the generated `CHANGELOG.md`.

## Usage

```bash
bash changelog.sh
bash changelog.sh --since v1.2.0
bash changelog.sh --output docs/CHANGELOG.md
```

Claude Code users can also run `/generate-changelog`.
