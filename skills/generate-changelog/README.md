# Generate Changelog Skill & CLI 📝

> Automated structured CHANGELOG generator from Git history following Conventional Commits and [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) standards.

## Quickstart in 3 Steps

### 1. Place in your project
Copy `skills/generate-changelog/` into your repository or Claude Code workspace.

### 2. Run the generator
```bash
# Auto-detects the latest git tag and generates/updates CHANGELOG.md:
python skills/generate-changelog/generate_changelog.py
```
*(Or via bash wrapper: `bash skills/generate-changelog/changelog.sh`)*

### 3. Verify output
Your `CHANGELOG.md` will contain cleanly categorized sections (`Added`, `Fixed`, `Changed`, `Performance`, `Security`, `Removed`) with commit links.

---

## Features
- **Auto-Categorization**: Converts `feat:` -> `Added`, `fix:` -> `Fixed`, `perf:` -> `Performance`, `security:` -> `Security`, `refactor:`/`chore:` -> `Changed`.
- **Zero Dependencies**: Pure Python 3 standard library (no `pip install` required).
- **Claude Code Native**: Trigger via `/generate-changelog` command in Claude Code.
- **Tag-Aware**: Automatically calculates diffs since the last git release tag (`git describe --tags --abbrev=0`).

---

## CLI Options

```bash
# Custom release version and date
python generate_changelog.py --version "v2.0.0" --date "2026-08-16"

# Preview output in terminal without modifying files
python generate_changelog.py --stdout

# Diff against a specific git tag or commit
python generate_changelog.py --since "v1.0.0"
```
