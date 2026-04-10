# CHANGELOG Generator — claude-builders-bounty#1

**Bounty:** $50 — powered by [Opire](https://opire.dev)  
**Issue:** [claude-builders-bounty#1](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1)

## Files

| File | Description |
|---|---|
| `generate-changelog.sh` | Bash script — works standalone |
| `SKILL-changelog.md` | Claude Code skill for `/generate-changelog` command |
| `README.md` | This file |

## Installation (3 steps)

```bash
# 1. Copy the script somewhere on your PATH
cp generate-changelog.sh /usr/local/bin/generate-changelog.sh
chmod +x /usr/local/bin/generate-changelog.sh

# 2. (Optional) Install the Claude Code skill
cp SKILL-changelog.md ~/.claude/skills/SKILL-changelog.md

# 3. Verify
generate-changelog.sh --help
```

## Quick Start

```bash
# Generate since the last git tag
bash generate-changelog.sh

# Generate since a specific version
bash generate-changelog.sh --since v1.0.0

# Write to custom file
bash generate-changelog.sh --output HISTORY.md
```

## Requirements

- `git`
- `awk`, `grep`, `sed` (standard on macOS/Linux; on Windows use WSL/Git Bash)

## Sample Output

See `CHANGELOG.sample.md` in this directory for a full example.

## Verified On

Tested on:
- macOS (bash 3.2+)
- Linux (bash 5.0+)
- Git Bash on Windows (MSYS2)
- GitHub Actions (ubuntu-latest)
