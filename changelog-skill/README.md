# CHANGELOG Generator

> A Claude Code skill and standalone bash script that generates structured `CHANGELOG.md` files from git history.

## Quick Start (3 Steps)

```bash
# 1. Clone or copy the skill files
git clone https://github.com/lee-muriithi-kingori/claude-builders-bounty.git changelog-generator
cd changelog-generator/changelog-skill

# 2. Make it executable
chmod +x changelog.sh

# 3. Run it in any git project
cd /path/to/your/project
/path/to/changelog.sh
```

That's it! Your `CHANGELOG.md` will be generated.

## Features

- **Auto-detects** the last git tag to determine commit range
- **Auto-categorizes** commits into: Added / Fixed / Changed / Removed
- **Follows** the [Keep a Changelog](https://keepachangelog.com/) format
- **De-duplicates** entries automatically
- **Works** with any git repository

## Usage Examples

```bash
# Basic usage - generates CHANGELOG.md
./changelog.sh

# Preview without writing to file
./changelog.sh --dry-run

# Custom output file
./changelog.sh --output HISTORY.md

# Specific date range
./changelog.sh --since 2026-01-01 --to 2026-06-30

# Mark as unreleased
./changelog.sh --unreleased

# Append to existing changelog
./changelog.sh --append

# Custom version
./changelog.sh --version 2.0.0
```

## Claude Code Integration

Add to your Claude Code skills:

```bash
# Copy SKILL.md to your Claude skills directory
cp SKILL.md ~/.claude/skills/changelog-generator.md
```

Then use in Claude Code:

```
/generate-changelog
```

## Testing

Tested on real GitHub repos:

```bash
# Test on any git repo
cd /path/to/any/git/repo
/path/to/changelog.sh --dry-run
```

## Requirements

- Git >= 2.20
- Bash >= 4.0
- POSIX utilities (grep, sed, awk, date)

## License

MIT
