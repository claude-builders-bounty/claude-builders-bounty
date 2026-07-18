# Changelog Generator

Generates a structured `CHANGELOG.md` from git history.

## Usage

```bash
bash generate-changelog.sh [output-file]
```

Default output: `CHANGELOG.md`

## How it works

- Fetches commits since the last git tag
- Auto-categorizes into: Added / Fixed / Changed / Removed / Documentation / Security / Performance
- Outputs a properly formatted `CHANGELOG.md`

## Requirements

- `git`
- A repository with at least one tag
