# Changelog Generator

A bash script and Claude Code skill that generates a structured `CHANGELOG.md` from git commit history.

## Setup (3 steps)

1. Clone and enter this repo:
   ```bash
   git clone <repo-url> && cd claude-builders-bounty
   ```

2. Make the script executable:
   ```bash
   chmod +x scripts/changelog.sh
   ```

3. Run it:
   ```bash
   bash scripts/changelog.sh
   ```

## What it does

- Fetches commits since the last git tag (or all commits if no tags)
- Auto-categorizes by conventional commit prefix into **Added / Fixed / Changed / Removed**
- Outputs a formatted `CHANGELOG.md`

## Claude Code Integration

Copy the skill to your skills directory:
```bash
cp -r skills/generate-changelog ~/.claude/skills/
```

Then use `/generate-changelog` in Claude Code.

## Requirements

- Git repo with at least one commit
- Bash 4+
- Best results with [Conventional Commits](https://www.conventionalcommits.org/) format
