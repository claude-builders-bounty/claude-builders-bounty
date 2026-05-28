---
name: generate-changelog
description: Auto-generate a structured CHANGELOG.md from git history, categorizing commits by type
version: 1.0.0
tags: [git, changelog, automation, release]
---

# Generate Changelog

Generates a structured `CHANGELOG.md` from a project's git history. Parses
commits since the most recent git tag and automatically categorizes them
into **Added**, **Fixed**, **Changed**, and **Removed** sections following
[Keep a Changelog](https://keepachangelog.com/) conventions.

## Quick Start

Add this skill to your project, then run:

```bash
bash changelog.sh
```

Or use the Claude Code slash command:

```
/generate-changelog
```

## Requirements

- `git` installed and available on PATH
- The repository must use git tags for versioning (e.g., `v1.0.0`, `1.2.3`)

## How It Works

1. Finds the most recent git tag (or uses the first commit if no tags exist)
2. Collects all commits between that tag and HEAD
3. Classifies each commit into categories based on conventional commit prefixes
   and keyword heuristics:
   - `Added` — `feat:`, `add`, `create`, `new`, `implement`
   - `Fixed` — `fix:`, `bug`, `resolve`, `patch`, `repair`
   - `Changed` — `refactor:`, `update`, `change`, `improve`, `optimize`, `upgrade`
   - `Removed` — `remove`, `delete`, `drop`, `deprecate`
4. Outputs a properly formatted `CHANGELOG.md`

## Output Format

```markdown
# Changelog

## [<new-version>] — <date>

### Added
- commit message

### Fixed
- commit message

### Changed
- commit message

### Removed
- commit message
```

## Customization

- Set the `NEXT_VERSION` environment variable to override the suggested version
- Edit the `PREFIXES` associative array in `changelog.sh` to adjust
  categorization rules
- Commits that don't match any category appear under **Changed** by default

## Testing

Tested on [Hermes Agent](https://github.com/NousResearch/hermes-agent),
a real-world project with 10,000+ commits and structured tag history.
