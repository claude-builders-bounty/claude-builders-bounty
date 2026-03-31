# SKILL.md — Generate Changelog

Generate a structured CHANGELOG.md from git history, auto-categorized into Added / Fixed / Changed / Removed.

## Trigger

- "generate changelog"
- "create changelog"
- "what changed since last release"
- `/generate-changelog`

## How To

Run the script:

```bash
bash skills/changelog/changelog.sh [output_file] [tag_prefix]
```

### Arguments

| Arg | Default | Description |
|-----|---------|-------------|
| `output_file` | `CHANGELOG.md` | Where to write the changelog |
| `tag_prefix` | *(empty)* | Tag prefix to filter (e.g. `v` for `v1.0.0`) |

### Examples

```bash
# Basic — uses latest tag, outputs to CHANGELOG.md
bash skills/changelog/changelog.sh

# Custom output path
bash skills/changelog/changelog.sh docs/CHANGELOG.md

# With tag prefix (e.g. tags are v1.0.0, v2.0.0)
bash skills/changelog/changelog.sh CHANGELOG.md v
```

## Output Format

```markdown
# Changelog

## [Unreleased] (since v1.2.0 — 2026-03-15)

### Added
- feat: add user authentication (`a1b2c3d`)

### Fixed
- fix: resolve null pointer on empty input (`e4f5g6h`)

### Changed
- refactor: simplify request parsing (`i7j8k9l`)

### Removed
- remove: drop deprecated v1 API endpoint (`m0n1o2p`)

### Other
- chore: update dependencies (`q3r4s5t`)
```

## Categorization Rules

Commits are categorized by their prefix/keyword:

| Category | Keywords |
|----------|----------|
| **Added** | add, feat, new, implement, create, support, initial |
| **Fixed** | fix, bug, resolve, patch, correct, repair, revert |
| **Changed** | change, update, refactor, improve, optimize, enhance, rename, move, doc |
| **Removed** | remove, delete, deprecate, drop, eliminate |
| **Other** | test, ci, build, chore, bump, release, merge |

## Requirements

- Bash 4+ (for arrays)
- Git repository with commit history
- Works on Linux, macOS, WSL
