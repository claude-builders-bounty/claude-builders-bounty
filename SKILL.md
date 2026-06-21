# SKILL: Generate a structured CHANGELOG from git history

## Overview
Generates a structured CHANGELOG.md from git history, categorizing commits into Added/Fixed/Changed/Removed sections.

## Usage

### Command
Run `/generate-changelog` or execute:
```bash
bash changelog.sh [repo_path] [since_tag] [output_file]
```

### Parameters
- `repo_path` (optional): Path to the git repository. Defaults to current directory.
- `since_tag` (optional): Git tag to start from. Defaults to latest tag, or all history.
- `output_file` (optional): Where to write CHANGELOG.md. Defaults to ./CHANGELOG.md.

## How It Works
1. Fetches commits from the last git tag (or all history if no tags)
2. Parses conventional commit messages to extract types (feat, fix, docs, etc.)
3. Categorizes each commit into:
   - **Added** — feat, feature
   - **Fixed** — fix, bugfix
   - **Changed** — refactor, style, change
   - **Performance Improvements** — perf
   - **Removed** — remove, del, rm
   - **Documentation** — docs, doc
   - **Chores** — chore, test, build, ci
   - **Other Changes** — everything else
4. Outputs a properly formatted CHANGELOG.md with markdown links to each commit

## Requirements
- Git
- Python 3.x (bundled with Git for Windows, or available on macOS/Linux)

## Tips
- Works best on repos using [Conventional Commits](https://www.conventionalcommits.org/)
- If no tags exist, generates changelog for entire repository history
- Can be run repeatedly; overwrites the output file each time
