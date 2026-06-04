# Generate Changelog

A Claude Code skill and bash script that automatically generates a structured `CHANGELOG.md` from git history.

## Quick Start

```bash
# Generate CHANGELOG.md from git history
bash generate-changelog.sh

# Or specify output file
bash generate-changelog.sh MY_CHANGELOG.md
```

## Features

- Works via `/generate-changelog` command (Claude Code skill)
- Falls back to `bash generate-changelog.sh`
- Fetches commits since the last git tag
- Auto-categorizes into: `Added` / `Fixed` `/ `Changed` / `Removed`
- Outputs a properly formatted `CHANGELOG.md`
- Uses conventional commit prefixes (feat, fix, change, remove, etc.)

## Setup (3 steps)

1. Clone any git repository
2. Run `bash generate-changelog.sh`
3. Check the generated `CHANGELOG.md`

## Acceptance Criteria

- [x] Works via `/generate-changelog` command or `bash changelog.sh`
- [x] Fetches commits since the last git tag
- [x] Auto-categorizes into: `Added` / `Fixed` / `Changed` / `Removed`
- [x] Outputs a properly formatted `CHANGELOG.md`
- [x] Tested on a real GitHub repo
- [x] README with setup instructions in 3 steps or fewer
