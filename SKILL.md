# CHANGELOG Generator Skill 📝

Automatically generate a structured `CHANGELOG.md` from your project's git history.

## Commands
- `/generate-changelog`: Fetches all commits since the last tag and categorizes them into `Added`, `Fixed`, `Changed`, and `Removed`.

## Features
- **Auto-categorization**: Intelligently parses commit messages using conventional commit patterns.
- **Smart Tag Detection**: Automatically finds the most recent git tag to determine the range.
- **Clean Formatting**: Produces a standard, readable Markdown file.
- **Multi-Interface**: Works via Claude Code command or standalone bash script.

## Usage (for Claude)
When asked to generate a changelog, run the following:
```bash
bash changelog.sh
```

## Manual Usage
```bash
./changelog.sh
```
