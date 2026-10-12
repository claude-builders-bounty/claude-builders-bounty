# Generate Changelog Skill 📝

An automated skill and CLI tool to parse git history, categorize commits following [Keep a Changelog](https://keepachangelog.com), and generate clean `CHANGELOG.md`.

## 🚀 Setup in 3 Steps:

1. **Copy into your project**:
   Copy `changelog.sh` (or `generate_changelog.py`) to your repository root or scripts directory.
2. **Make executable**:
   ```bash
   chmod +x changelog.sh
   ```
3. **Run**:
   ```bash
   bash changelog.sh
   # or with Claude Code:
   /generate-changelog
   ```

## ✨ Acceptance Criteria Fulfilled:
- [x] Works via `/generate-changelog` command or `bash changelog.sh` (and cross-platform Python)
- [x] Fetches commits since the last git tag (or from root commit if untagged)
- [x] Auto-categorizes into: `Added`, `Fixed`, `Changed`, `Removed`
- [x] Outputs a properly formatted, compliant `CHANGELOG.md`
- [x] Tested on a real repository with sample output included
- [x] Simple 3-step setup guide
