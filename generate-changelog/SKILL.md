# generate-changelog

Generate a structured `CHANGELOG.md` from the project's git history.

## Usage

```
/generate-changelog
```

Or with options:

```
/generate-changelog --tag v1.0.0
/generate-changelog --repo /path/to/repo
```

## What it does

1. Finds the last git tag (or uses `--tag`)
2. Groups commits by type: Added / Fixed / Changed / Removed
3. Writes a formatted `CHANGELOG.md`

## Requirements

Python 3.6+, git on PATH.
