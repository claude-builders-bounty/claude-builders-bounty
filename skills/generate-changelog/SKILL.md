# Generate Changelog

Automatically generates a structured `CHANGELOG.md` from a project's git history.

## Usage

In Claude Code, type:

```
/generate-changelog
```

Or run directly:

```bash
bash changelog.sh
```

## What It Does

1. Fetches all commits since the last git tag (or from repo start if no tags exist)
2. Auto-categorizes each commit into: `Added`, `Fixed`, `Changed`, `Removed`
3. Outputs a properly formatted `CHANGELOG.md`
4. Preserves existing changelog entries by prepending new entries

## Categorization Rules

| Category | Commit message patterns |
|----------|------------------------|
| **Added** | `feat:`, `add:`, `new:`, `feature:` |
| **Fixed** | `fix:`, `bug:`, `patch:`, `hotfix:` |
| **Changed** | `refactor:`, `update:`, `change:`, `improve:`, `perf:`, `chore:` |
| **Removed** | `remove:`, `delete:`, `deprecate:` |

Commits not matching any pattern are placed under **Changed**.

## Arguments

- `/generate-changelog [version]` — specify version label (default: auto-incremented from last tag)
- `/generate-changelog --from <ref>` — start from a specific ref instead of last tag

## Example Output

```markdown
# Changelog

## [1.2.0] - 2026-05-20

### Added
- feat: add user authentication flow
- feat: implement password reset

### Fixed
- fix: resolve crash on empty cart
- fix: patch CORS header for staging

### Changed
- refactor: simplify database connection pooling
- chore: update dependencies

### Removed
- remove: deprecated legacy API endpoints
```

## Installation

```bash
# Option 1: Copy SKILL.md to your project
cp SKILL.md /path/to/project/.claude/skills/generate-changelog/SKILL.md

# Option 2: Run the standalone script
bash changelog.sh
```