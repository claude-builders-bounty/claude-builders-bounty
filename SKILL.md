# Generate Changelog Skill

A Claude Code skill that automatically generates a structured `CHANGELOG.md` from git history.

## Usage

```
/generate-changelog [output-file]
```

If no output file is specified, creates `CHANGELOG.md` in the current directory.

## What it does

1. Reads git history and identifies commits since the last tag
2. Auto-categorizes commits into: Added / Fixed / Changed / Removed
3. Outputs a properly formatted Markdown changelog
4. Handles repos with no tags (uses chronological order)

## Features

- **Conventional commit aware**: Recognizes `feat:`, `fix:`, `chore:`, `docs:`, etc.
- **Semantic version tag support**: Groups changes by version (v1.0.0, v2.3.1)
- **Fallback for untagged repos**: Lists all commits chronologically
- **Clean Markdown output**: Proper headers, links, and formatting

## Requirements

- Git repository with at least one commit
- Bash shell

## Examples

```bash
# Generate CHANGELOG.md in current directory
bash changelog.sh

# Generate to a specific file
bash changelog.sh docs/CHANGELOG.md
```

## Acceptance Criteria

- [x] Works via `bash changelog.sh` command
- [x] Fetches commits since the last git tag
- [x] Auto-categorizes into: Added / Fixed / Changed / Removed
- [x] Outputs a properly formatted `CHANGELOG.md`
- [x] Tested on a real GitHub repo (this repository)
- [x] README with setup instructions in 3 steps or fewer
