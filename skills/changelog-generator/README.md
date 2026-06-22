# Auto Changelog Generator

Generate structured CHANGELOG.md from git history in one command.

## Setup

1. Download `changelog.sh`
2. `chmod +x changelog.sh`
3. `./changelog.sh /path/to/repo`

## Features

- Auto-categorizes commits: Added / Fixed / Changed / Removed
- Fetches since last git tag (or all commits if no tags)
- Outputs standard Keep-a-Changelog format
- Tested on zeroeye (50+ commits) — see sample output in PR

## Sample Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [v2026.06.23] - 2026-06-23

### Added
- feat: add user authentication with OAuth2 support
- feat: add rate limiter token bucket with sliding window
...
```
