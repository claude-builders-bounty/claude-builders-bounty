# CLAUDE.md Skill: Generate Changelog

## Instructions

When the user asks to generate a changelog, run:

```bash
bash changelog.sh
```

### Options

- `bash changelog.sh --tag v1.0.0` — changelog from a specific tag
- `bash changelog.sh --since "2025-01-01"` — changelog from a date
- `bash changelog.sh --all` — all commits
- `bash changelog.sh --output RELEASE_NOTES.md` — custom filename

### What it does

Reads git log and categorizes commits into Added / Fixed / Changed / Removed / Other sections in a `CHANGELOG.md` file.
