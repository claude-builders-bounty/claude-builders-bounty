# SKILL: Generate a Structured CHANGELOG from Git History

Generate a structured, categorized CHANGELOG.md from a project's git commit history.

## Trigger

User asks to generate a changelog, release notes, or version history. Examples:
- "Generate a changelog for this project"
- "Create release notes since the last tag"
- "What's changed since v1.0?"

## Implementation

Run the bundled `changelog.sh` script:

```bash
bash skills/changelog-generator/changelog.sh [--since <tag>] [--output <file>] [--limit <n>]
```

## Categorization Logic

Commits are auto-categorized using Conventional Commits prefixes:

| Prefix | Category |
|--------|----------|
| `feat:`, `feature:`, `add:`, `added:` | **Added** |
| `fix:`, `bug:`, `hotfix:`, `patch:` | **Fixed** |
| `refactor:`, `perf:`, `style:`, `chore:`, `ci:`, `build:`, `test:`, `docs:`, `revert:` | **Changed** |
| `remove:`, `delete:`, `drop:`, `deprecate:` | **Removed** |

For non-conventional commits, keyword matching is used as a fallback:
- Contains `fix`, `bug`, `resolve` → **Fixed**
- Contains `add`, `new`, `introduce`, `create` → **Added**
- Contains `remove`, `delete`, `drop` → **Removed**
- Contains `update`, `change`, `refactor`, `improve` → **Changed**

## Output Format

```markdown
# Changelog

## [Unreleased]

### Added
- New user authentication system (abc1234)

### Fixed
- Login redirect issue on mobile (def5678)

### Changed
- Updated dependencies to latest versions (ghi9012)

### Removed
- Dropped deprecated v1 API endpoints (jkl3456)

---
_Generated on 2026-05-21 from 100 commits._
```

## Options

- `--since TAG` — Start from a specific git tag (default: last tag, or beginning)
- `--output FILE` — Write to custom output file (default: CHANGELOG.md)
- `--limit N` — Maximum commits to process (default: 100)
- `--help` — Show usage help

## Edge Cases Handled

- Empty repositories (generates empty changelog with note)
- No prior tags (processes all commits)
- Merge commits (filtered out automatically)
- Non-conventional commit messages (keyword fallback)
- Existing CHANGELOG (appends to beginning, preserving history)
