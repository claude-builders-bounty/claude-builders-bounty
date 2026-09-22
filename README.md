# Git Changelog Generator Skill

A lightweight, portable tool and Claude Code Skill to automatically generate a structured CHANGELOG.md from git commits following Keep a Changelog.

## Quick Setup (3 Steps)

1. Clone or Copy: Place changelog.sh and SKILL.md into your repository root.
2. Make Executable: Run chmod +x changelog.sh (on Linux/macOS/Git Bash).
3. Run:
   - Claude Code: run /generate-changelog
   - Terminal: run bash changelog.sh

## Features
- Tag-aware: Fetches changes since the latest git tag (falls back cleanly to all history if no tags exist).
- Auto-categorization: Automatically groups commits into Added, Fixed, Changed, and Removed.
- Non-destructive: Prepends new entries while preserving existing changelog history.
