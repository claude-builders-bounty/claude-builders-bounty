# /generate-changelog

Generate a structured `CHANGELOG.md` from git history.

## Usage

```
/generate-changelog
```

Or from bash:

```bash
bash changelog.sh --since v1.0.0 --output CHANGELOG.md
```

## What it does

1. Fetches commits since the last git tag (or all commits if no tag exists)
2. Auto-categorizes into: **Added**, **Fixed**, **Changed**, **Removed**
3. Uses conventional commit prefixes (`feat:`, `fix:`, `chore:`, etc.)
4. Outputs a properly formatted `CHANGELOG.md` in [Keep a Changelog](https://keepachangelog.com/) style

## Requirements

- `git` available in PATH
- Bash 4+

## Files

- `changelog.sh` — standalone bash script
