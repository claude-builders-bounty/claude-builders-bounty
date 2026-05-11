# CHANGELOG Generator

Auto-generate structured `CHANGELOG.md` from git history.

## Setup (3 steps)

### 1. Copy the script
```bash
cp changelog.sh /usr/local/bin/generate-changelog
chmod +x /usr/local/bin/generate-changelog
```

### 2. (Optional) Install as Claude Code skill
Copy `SKILL.md` to your project's `.claude/skills/` directory:
```bash
mkdir -p .claude/skills/
cp SKILL.md .claude/skills/generate-changelog.md
```

### 3. Run it
```bash
# In any git repo:
generate-changelog

# Or with Claude Code:
/generate-changelog
```

## Requirements

- `bash` (any version)
- `git` (any version)
- No other dependencies

## How it works

1. Finds the most recent git tag
2. Collects all non-merge commits since that tag
3. Classifies each commit by its conventional commit prefix
4. Outputs a Keep-a-Changelog-compliant CHANGELOG.md

## Tested on

- Linux (Ubuntu 22.04, CentOS 7)
- macOS (Ventura, Sonoma)
- Git repos: small (50 commits) to large (5000+ commits)
