# Solution README — Issue #1: CHANGELOG Generator

## Bounty
**[$50 USD] SKILL: Generate a structured CHANGELOG from git history**
[Issue #1](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1)

## Solution
`generate_changelog.py` — A standalone Python script that parses git log history and generates a structured CHANGELOG.md following the [Keep a Changelog](https://keepachangelog.com/) format.

## Usage
```bash
# Generate CHANGELOG.md for current repo
python3 generate_changelog.py

# Specify repo path and output file
python3 generate_changelog.py --repo /path/to/repo --output CHANGELOG.md

# Only include commits after a specific tag
python3 generate_changelog.py --since v1.0.0

# Print to stdout instead of writing a file
python3 generate_changelog.py --stdout
```

## Features
- Parses **conventional commits** (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `perf:`, `test:`, `style:`, `ci:`, `build:`, `revert:`, `security:`)
- Groups commits by **version tag intervals** (uses `git tag --format` to detect boundaries)
- Handles **merge commits** (excluded from grouped output)
- Handles **non-conventional commits** (grouped under "Other Changes")
- Handles **breaking changes** (`feat!:` and `refactor(scope)!:` syntax)
- Includes **commit scope** in output (e.g., `fix(api): correct status code`)
- Truncates long descriptions (80 char limit)
- Shows **short commit hashes** (7 chars) for traceability
- Gracefully handles **empty repos**, **missing tags**, and **empty commit ranges**

## Output Format
```markdown
# Changelog
All notable changes...

## [Unreleased]
### ✨ Features
- add user authentication (`abc1234`)

### 🐛 Bug Fixes
- **api:** correct response status code (`def5678`)

## [v1.0.0] - 2026-07-15
### ✨ Features
- initial release (`ghi9012`)
```

## Testing
```bash
pytest tests/test_solutions/test_issue_1_changelog.py -v
```
23 tests covering commit parsing, version grouping, markdown generation, and end-to-end with mocked git.
