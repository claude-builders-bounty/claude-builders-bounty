# 🏷️ Generate Changelog — Claude Code Skill

Generate a structured `CHANGELOG.md` from git history with automatic commit categorization.

## ✨ Features

- Parses **Conventional Commits** (`feat:`, `fix:`, `refactor:`, etc.)
- Falls back to **keyword detection** for non-conventional commits
- Groups commits into: Added, Fixed, Changed, Deprecated, Removed, Security, Documentation, Testing
- Includes commit SHA links, contributor counts, and stats
- Works as a Claude Code command **and** standalone bash script

## 🚀 Setup

### Option 1: Claude Code command

```
# Copy the command definition
cp .claude/commands/generate-changelog.md ~/.claude/commands/
```

Then in Claude Code: `/generate-changelog`

### Option 2: Standalone bash

```bash
bash changelog.sh
```

### Option 3: Direct Python

```bash
python scripts/generate_changelog.py -o CHANGELOG.md
```

## 📋 Requirements

- Python 3.8+
- Git repository

## 🧪 Testing

```bash
python -m unittest discover -s tests
```

## 📄 Example Output

See [`examples/sample-output.md`](examples/sample-output.md) for a generated example.

## 🔧 Advanced Usage

```bash
# Generate from a specific tag
python scripts/generate_changelog.py -t v1.0.0 -o CHANGELOG.md

# Generate with a custom version string
python scripts/generate_changelog.py -v "2.0.0-beta" -o CHANGELOG.md

# Specify a different git repo
python scripts/generate_changelog.py -c /path/to/other/repo -o CHANGELOG.md

# Preview without writing
python scripts/generate_changelog.py
```
