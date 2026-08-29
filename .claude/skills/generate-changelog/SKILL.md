---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the last tag
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
---

# Generate Changelog Skill

Generate a structured CHANGELOG.md from git history since the last tag.

## Usage

```
# Via slash command (recommended)
/generate-changelog

# Or directly via bash script
bash .claude/skills/generate-changelog/changelog.sh
```

## What it does

1. Validates the current directory is a git repository
2. Finds the latest git tag (annotated or lightweight)
3. Fetches all commits since that tag (or all commits if no tags exist)
4. Categorizes commits into: Added, Fixed, Changed, Removed
5. Generates/updates a professional CHANGELOG.md file

## Classification Strategy

The classification uses a **deterministic, priority-based approach**:

### 1. Conventional Commits (highest priority)

Parses the conventional commit prefix `type(scope): subject` and maps each type:

| Conventional Type | Category | Priority |
|-------------------|----------|----------|
| `fix`, `bug`, `hotfix`, `patch` | Fixed | 1 (highest) |
| `remove`, `delete`, `drop`, `rm` | Removed | 2 |
| `feat`, `feature` | Added | 3 |
| `refactor`, `refact`, `perf`, `optimize`, `improve`, `enhance`, `style`, `format`, `test`, `tests`, `docs`, `doc`, `chore`, `build`, `ci`, `cd` | Changed | 4 |
| `revert` | Removed | 5 |
| `breaking` (or `BREAKING CHANGE` in body) | Changed | 6 |

### 2. Multi-Intent Commits

If a commit subject contains multiple type-like keywords (e.g., "Fix authentication and remove legacy endpoint"), the **priority order** determines the category:

```
fix > remove > feat > refactor/perf/style/test/docs/chore > breaking
```

This ensures deterministic, predictable classification.

### 3. Non-Conventional Commits (fallback)

For commits without a conventional prefix, only the **subject line** is analyzed (not the body) using precise word-boundary matching:

- **Added**: `add`, `create`, `implement`, `introduce`, `new` (at start or after `:`/`;`/`,`)
- **Fixed**: `fix`, `bug`, `patch`, `hotfix`, `resolve`, `correct`, `repair` (at start or after `:`/`;`/`,`)
- **Removed**: `remove`, `delete`, `drop`, `deprecate`, `eliminate` (at start or after `:`/`;`/`,`)
- **Changed**: `update`, `change`, `modify`, `improve`, `enhance`, `optimize`, `refactor`, `migrate`, `upgrade`, `reorganize`, `restructure` (at start or after `:`/`;`/`,`)
- **Default**: `Changed`

This prevents false positives like:
- `test: add authentication tests` → **Changed** (type `test` maps to Changed)
- `docs: update README` → **Changed** (type `docs` maps to Changed)

## Output Format

```markdown
# Changelog

## [Unreleased] - YYYY-MM-DD

### Added
- Commit subject (hash)

### Fixed
- Commit subject (hash)

### Changed
- Commit subject (hash)

### Removed
- Commit subject (hash)
```

## Behavior with Existing CHANGELOG.md

If CHANGELOG.md already exists:
- Updates the existing `[Unreleased]` section in place
- Preserves all previous release sections
- Creates a backup at `CHANGELOG.md.backup` before modifying
- **Never creates duplicate `# Changelog` headers** - checks if header exists before adding

If no `[Unreleased]` section exists, prepends a new one while preserving existing content.

## Edge Cases

- **No tags**: Uses all commits from repository history
- **No commits since tag**: Creates empty sections with "(none)" placeholder
- **Not a git repo**: Clear error message with exit code 1
- **Special characters**: Handles `|`, `"`, `'`, `$`, `:`, `&`, `()`, newlines, tabs in subjects/bodies
- **Multi-line bodies**: Correctly parses without creating phantom commits

## Parsing Approach (Robust)

Uses **NUL byte (`%x00`) delimiters** in git log format:
```
git log --pretty=format:"%h%x00%s%x00%b%x00" --reverse
```

This is immune to:
- `|` in subject or body
- Multi-line bodies
- Any special characters
- Empty bodies

Reads commits using `IFS= read -r -d ''` to properly handle NUL delimiters without stripping.

## Requirements

- Bash (for the script)
- Git (for commit history)
- No external dependencies

## Installation (3 steps)

1. Copy the skill to your project:
   ```bash
   mkdir -p .claude/skills/generate-changelog
   cp /path/to/generate-changelog/SKILL.md .claude/skills/generate-changelog/
   cp /path/to/generate-changelog/changelog.sh .claude/skills/generate-changelog/
   ```

2. Make the script executable:
   ```bash
   chmod +x .claude/skills/generate-changelog/changelog.sh
   ```

3. Run it:
   ```bash
   # Via slash command (recommended)
   /generate-changelog
   
   # Or directly via bash
   bash .claude/skills/generate-changelog/changelog.sh
   ```

## Execution Instructions

The skill provides two ways to execute:

### Method 1: Slash Command (Recommended)
```
/generate-changelog
```
This invokes the skill through the Claude Code interface and runs the script in the current working directory.

### Method 2: Direct Bash Execution
```bash
bash .claude/skills/generate-changelog/changelog.sh
```
Run this from the root of your git repository. The script will:
1. Auto-detect the latest tag
2. Process all commits since that tag
3. Generate/update CHANGELOG.md in the current directory

### Method 3: From Any Directory (using absolute path)
```bash
bash /full/path/to/.claude/skills/generate-changelog/changelog.sh
```
The script uses git commands that work from any subdirectory of the repo.

## Example Output

```markdown
# Changelog

## [Unreleased] - 2026-08-29

### Added
- feat: add user authentication (867a79f)

### Fixed
- fix: resolve token expiration (047b960)

### Changed
- refactor: reorganize authentication service (4fafc24)
- Update authentication flow (8d1d825)

### Removed
- remove deprecated endpoint (3e294e5)
- Delete legacy endpoint (78ce55e)
```

## Example Classification

| Commit Message | Category | Reason |
|----------------|----------|--------|
| `feat: add user authentication` | Added | Conventional `feat` |
| `fix: resolve token expiration` | Fixed | Conventional `fix` |
| `refactor: reorganize authentication service` | Changed | Conventional `refactor` |
| `remove deprecated endpoint` | Removed | Conventional `remove` |
| `Update authentication flow` | Changed | Fallback keyword `update` |
| `Improve error handling` | Changed | Fallback keyword `improve` |
| `Delete unused configuration` | Removed | Fallback keyword `delete` |
| `test: add authentication tests` | Changed | Conventional `test` → Changed |
| `docs: update README` | Changed | Conventional `docs` → Changed |
| `chore: update dependencies` | Changed | Conventional `chore` → Changed |
| `Fix auth and remove legacy endpoint` | Fixed | Multi-intent: fix > remove |
| `feat: add feature and fix bug` | Fixed | Multi-intent: fix > feat (fix wins) |

*Started by the Claude builder community · March 2026 · MIT License*