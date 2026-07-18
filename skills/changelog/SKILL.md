# Changelog Generator

Generate a structured CHANGELOG.md from git history.

## Usage

```
/generate-changelog
```

Or:

```bash
bash changelog.sh
```

## Behavior

- Fetches commits since the last git tag
- Auto-categorizes into: Added / Fixed / Changed / Removed
- Outputs `CHANGELOG.md` in Keep a Changelog format
- Supports conventional commit prefixes (feat:, fix:, chore:, etc.)
