# Generate Changelog

Generate a structured `CHANGELOG.md` from git history since the last tag.

## Trigger

Use `/generate-changelog` in Claude Code, or run:

```bash
bash changelog.sh
```

## Behavior

1. Detect the latest git tag (or all commits if none).
2. Collect commits since that tag.
3. Categorize subjects into Added, Fixed, Changed, Removed.
4. Write a formatted `CHANGELOG.md` in the repo root.

## Files

- `changelog.sh` — standalone bash generator
- `samples/CHANGELOG.sample.md` — example output from this repo

## Setup

```bash
chmod +x changelog.sh
bash changelog.sh .
```
