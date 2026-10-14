# Git History Structured Changelog Generator

Automatically generates a structured, industry-standard `CHANGELOG.md` from a repository's git commits since the last tag.

## Features
- Detects the latest git tag automatically (falls back to initial commit).
- Auto-categorizes into `Added`, `Fixed`, `Changed`, and `Removed`.
- Native bash script and Claude Code / Hermes skill wrapper.
- Verified on live Git repositories.

## Quick Setup (3 Steps)

1. **Install Script**:
   Copy `changelog.sh` into your repository root or `scripts/` directory:
   ```bash
   chmod +x changelog.sh
   ```

2. **Generate Changelog**:
   Run the command:
   ```bash
   bash changelog.sh CHANGELOG.md
   ```

3. **Verify**:
   Open `CHANGELOG.md` to see categorized release notes with commit hashes.
