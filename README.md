# Changelog Generator

Automatically generates `CHANGELOG.md` from git history, categorized by commit type.

## Setup (3 steps)

```bash
# 1. Download the script
curl -sL https://raw.githubusercontent.com/kiknaio/claude-hooks-bounty/main/changelog.sh -o changelog.sh

# 2. Make it executable
chmod +x changelog.sh

# 3. Run it in any git repo
bash changelog.sh
```

## What it does

- Fetches commits since last git tag (or all commits if no tags)
- Auto-categorizes into: **Added** / **Fixed** / **Changed** / **Removed**
- Outputs properly formatted `CHANGELOG.md` (Keep a Changelog format)

## Sample output

See `sample-CHANGELOG.md` for example output from a real repo.

## Requirements

- Bash
- Git
