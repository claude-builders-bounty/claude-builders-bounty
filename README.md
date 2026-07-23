# Changelog Generator Skill

Generates a structured CHANGELOG.md from git history.

## Setup (3 steps)

1. Copy `changelog.sh` to your project
2. `chmod +x changelog.sh`
3. Run `./changelog.sh` or `./changelog.sh /path/to/repo`

## Features
- Auto-detects last git tag
- Categorizes commits as Added/Fixed/Changed/Removed
- Includes commit hash references
- Works on any git repo

## Test
```bash
cd ~/projects/saas-starter && ~/projects/changelog-skill/changelog.sh
```
