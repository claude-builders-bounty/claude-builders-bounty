---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history. Trigger: "generate changelog", "create changelog", "/generate-changelog"
allowed-tools:
  - Bash
---

# 📝 SKILL: Generate CHANGELOG from Git History

This skill automatically generates a structured `CHANGELOG.md` file from your git commit history.

## How to Use

**Via Claude Code command:**
```
/generate-changelog
```

**Or manually via bash:**
```bash
./scripts/generate-changelog.sh
```

## Features

- Automatically fetches commits since the last git tag
- Categorizes commits into: Added, Changed, Fixed, Removed
- Outputs properly formatted CHANGELOG.md (Keep a Changelog format)
- Works with any git repository

## Acceptance Criteria (Bounty #1)

- [x] Works via `/generate-changelog` command or `bash changelog.sh`
- [x] Fetches commits since the last git tag
- [x] Auto-categorizes into: `Added` / `Fixed` / `Changed` / `Removed`
- [x] Outputs a properly formatted `CHANGELOG.md`
- [x] Tested on a real GitHub repo (this repo!)
- [x] README with setup instructions (3 steps or less)

## Example Output

See `CHANGELOG.md` in this repository for a sample output.

## Setup (3 steps)

1. Clone this skill to your project:
   ```bash
   curl -O https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/scripts/generate-changelog.sh
   ```

2. Make executable:
   ```bash
   chmod +x scripts/generate-changelog.sh
   ```

3. Run:
   ```bash
   ./scripts/generate-changelog.sh
   ```

## Stack

- Bash script (no dependencies)
- Optional: Python for advanced parsing (if available)
