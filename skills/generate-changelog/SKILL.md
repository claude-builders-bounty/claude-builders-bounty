# Generate CHANGELOG from git history

Use `bash ./changelog.sh` to generate a `CHANGELOG.md` from the current repository's git history.

## What it does
- Detects the latest git tag automatically
- Collects commits since that tag
- Categorizes entries into `Added`, `Fixed`, `Changed`, and `Removed`
- Writes a Keep a Changelog style `CHANGELOG.md`

## Usage
```bash
bash ./changelog.sh
bash ./changelog.sh --repo /path/to/repo --output /tmp/CHANGELOG.md
bash ./changelog.sh --tag v1.2.3
```

## Notes
- If the repository has no tags, the full history is used.
- Conventional commits are parsed directly and non-conventional commits fall back to keyword matching.
- Commit links are included automatically for GitHub remotes.
