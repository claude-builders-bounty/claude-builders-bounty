# Generate Changelog

A skill and bash script to automatically generate a structured `CHANGELOG.md` from a project's git history. It intelligently groups commits into `Added`, `Fixed`, `Changed`, and `Removed` categories.

## Setup Instructions

Choose **one** of the following methods:

### Method 1: Using Claude Code Skill (Recommended)
1. Copy the `SKILL.md` into your project's `.claudecode/skills/generate-changelog/` directory.
2. In your terminal running Claude Code, type `/generate-changelog`.
3. Claude will fetch the latest commits since the last tag, categorize them using its LLM reasoning, and create a properly formatted `CHANGELOG.md`.

### Method 2: Using the Bash Script
1. Copy `changelog.sh` into your project directory.
2. Make it executable: `chmod +x changelog.sh`
3. Run the script: `./changelog.sh` (or `bash changelog.sh`) to instantly output a `CHANGELOG.md` based on commit message keywords.

## Features
- Automatically finds the last git tag and fetches commits since then.
- Auto-categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Outputs a clean, standard Markdown format for `CHANGELOG.md`.
