# Changelog Generator 📋

> **Bounty: $50** — [Issue #1](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1)

Generate a structured, categorized `CHANGELOG.md` from git history in 1 command.

## Setup (3 steps)

```bash
# 1. Copy the skill to your project
cp -r changelog-bounty /path/to/your/project/.claude/skills/

# 2. Run the script
cd /path/to/your/project
bash changelog-bounty/changelog.sh

# 3. Done! Check CHANGELOG.md
cat CHANGELOG.md
```

## Usage

### Option A: Bash Script
```bash
bash changelog.sh              # writes to CHANGELOG.md
bash changelog.sh HISTORY.md   # writes to custom filename
```

### Option B: Claude Code / OpenClaw
Type `/generate-changelog` in any git repository.

## What It Does

1. Finds the last git tag (`git describe --tags --abbrev=0`)
2. Fetches all commits since that tag (no merges)
3. Classifies each commit into sections:

| Section    | Prefixes                                    |
|------------|---------------------------------------------|
| **Added**  | `feat:`, `add:`, `implement:`, `create:`    |
| **Fixed**  | `fix:`, `bug:`, `correct:`, `hotfix:`       |
| **Changed**| `refactor:`, `perf:`, `update:`, `improve:` |
| **Removed**| `remove:`, `delete:`, `deprecate:`, `drop:` |

4. Falls back to keyword heuristics for non-conventional commits
5. Writes or merges into `CHANGELOG.md`

## Output Example

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- feat: add user authentication with OAuth2 (abc1234)
- implement rate limiting middleware (def5678)

### Fixed
- fix: resolve null pointer in user profile (ghi9012)

### Changed
- refactor: migrate database queries to prepared statements (jkl3456)

### Removed
- deprecate legacy API v1 endpoints (mno7890)
```

## Sample Output

The `SAMPLE_OUTPUT.md` file shows the real output generated from the `claude-builders-bounty` repo itself.

## Requirements

- **git** (any version)
- **bash** 4.0+
- No API keys, no network, no npm install

## File Structure

```
changelog-bounty/
├── SKILL.md         # Agent skill definition
├── changelog.sh     # The generator script
├── README.md        # This file
└── SAMPLE_OUTPUT.md # Real output from this repo
```
