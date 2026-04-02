# CHANGELOG Generator Skill — Submission for Issue #1 ($50)

## Overview

This submission implements a complete SKILL for generating `CHANGELOG.md` from git history, auto-categorizing commits into: Added / Fixed / Changed / Removed / Other.

## Files

- `changelog.sh` — The main bash script that parses git history and generates CHANGELOG.md
- `SKILL.md` — Claude Code skill definition (invokes via `/generate-changelog`)
- `SAMPLE-CHANGELOG.md` — Example output

## Features

✅ Works via `/generate-changelog` command  
✅ Fetches commits since the last git tag (or all commits if no tag)  
✅ Auto-categorizes into: Added / Fixed / Changed / Removed / Other  
✅ Outputs properly formatted CHANGELOG.md  
✅ Zero dependencies (only `git`, `bash`, `sort`, `uniq`)  
✅ No external API calls  
✅ Tested on this repo  

## Usage

```bash
# Quick start — generate CHANGELOG.md from all commits
bash changelog.sh

# Generate from a specific tag
bash changelog.sh --from-tag v1.0.0

# Output to a different file
bash changelog.sh --output HISTORY.md
```

## In Claude Code

Copy `SKILL.md` to your project's `.claude/skills/` directory and invoke with `/generate-changelog`.

## Bounty

- Issue: #1
- Bounty: $50
-收款地址：eB51DWp1uECrLZRLsE2cnyZUzfRWvzUzaJzkatTpQV9