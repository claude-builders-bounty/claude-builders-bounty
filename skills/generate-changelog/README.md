# 🗒️ Generate CHANGELOG from git history

A Claude Code skill + bash script that generates a structured `CHANGELOG.md` from your project's git history.

## 3-Step Setup

```bash
# 1. Copy the skill to your Claude Code skills directory
cp -r skills/generate-changelog ~/.claude/skills/

# 2. Make the script executable
chmod +x ~/.claude/skills/generate-changelog/changelog.sh

# 3. Run it!
cd your-project && ~/.claude/skills/generate-changelog/changelog.sh
```

## Usage

```bash
# Generate since last tag
./changelog.sh

# Generate from a specific tag
./changelog.sh --since-tag v1.2.0

# Dry run (preview only)
./changelog.sh --dry-run

# All commits (no tag filtering)
./changelog.sh --all

# Different output file
./changelog.sh --output HISTORY.md
```

## Features

- ✅ Auto-categorizes commits: Added / Fixed / Changed / Removed
- ✅ Uses conventional commit prefixes (feat, fix, chore, etc.)
- ✅ Respects git tags (only new commits since last release)
- ✅ Breaking changes detected and listed in Removed
- ✅ Works standalone — no dependencies beyond `git` + `bash`
- ✅ Cross-platform (macOS + Linux)
- ✅ Copy as SKILL.md for Claude Code native command

## Files

```
skills/generate-changelog/
├── SKILL.md          # Claude Code skill (activates on /generate-changelog)
├── changelog.sh      # Standalone bash script
├── README.md         # This file
└── sample-output.md  # Sample output from this repo
```

## How It Works

| Commit prefix | Category |
|---------------|----------|
| `feat:` `feat()` | **Added** |
| `fix:` `fix()` | **Fixed** |
| `chore:` `docs:` `style:` `refactor:` | **Changed** |
| `BREAKING CHANGE` | **Removed** |
| *(everything else)* | **Changed** |

## Requirements

- `git`
- `bash 4.0+`
- `sed` (GNU sed recommended, macOS sed also works)
