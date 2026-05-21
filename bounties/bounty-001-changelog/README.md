# CHANGELOG Generator

Generate a structured `CHANGELOG.md` from git history in 3 steps.

## Setup

```bash
# 1. Save the script
curl -O https://raw.githubusercontent.com/a918124259a/claude-builders-bounty/main/bounties/bounty-001-changelog/changelog.sh

# 2. Make it executable
chmod +x changelog.sh

# 3. Run it in your project
bash changelog.sh /path/to/your/project
```

## Output

The script creates `CHANGELOG.md` with categorized entries:

```
# Changelog

## [Unreleased]

### ✨ Added
- New user dashboard (abc1234)
- API rate limiting (def5678)

### 🐛 Fixed
- Login crash on null token (ghi9012)
```

## Claude Code Integration

Add the SKILL.md to your project for `/generate-changelog` command support.
