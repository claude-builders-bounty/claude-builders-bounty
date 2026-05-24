# Changelog Generator

A CLI tool to automatically generate a structured `CHANGELOG.md` from git history.

## Setup (3 Steps)

**1. Make the script executable**
```bash
chmod +x changelog.sh
```

**2. Run the script**
```bash
./changelog.sh
```

**3. Check your CHANGELOG.md**
```bash
cat CHANGELOG.md
```

## Features

- Auto-detects the most recent git tag and generates changelog from that point
- Falls back to the last 30 commits if no tags exist
- Parses conventional commits (`feat:`, `fix:`, `docs:`, etc.)
- Categorizes changes into: Added / Fixed / Changed / Removed
- Outputs properly formatted Markdown

## Claude Code Integration

Use the `/generate-changelog` command in Claude Code to invoke this skill.

## Requirements

- Git
- Bash (Linux/macOS) or Git Bash (Windows)