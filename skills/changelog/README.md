# Changelog Generator

Generate structured CHANGELOG.md from git history.

## Setup (3 steps)

1. Clone or copy `skills/changelog/` into your project
2. Make the script executable: `chmod +x skills/changelog/changelog.sh`
3. Run it: `bash skills/changelog/changelog.sh`

## Usage

```bash
# Generate changelog for current repo
bash skills/changelog/changelog.sh

# Generate changelog for a specific repo
bash skills/changelog/changelog.sh /path/to/repo

# Output to file
bash skills/changelog/changelog.sh > CHANGELOG.md

# With Claude Code
/generate-changelog
```

## How it works

- Finds the last git tag (or uses all commits if no tags)
- Parses Conventional Commits prefixes (`feat:`, `fix:`, `refactor:`, etc.)
- Categorizes into Added / Fixed / Changed / Removed
- Outputs markdown formatted for GitHub

## Requirements

- Git (any version)
- Bash 4+ (for arrays)
