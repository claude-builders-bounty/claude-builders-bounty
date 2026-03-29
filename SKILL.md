# SKILL: Generate a Structured CHANGELOG from Git History

Generate a structured `CHANGELOG.md` from a project's git history. Works as a Claude Code skill invoked via `/generate-changelog` or as a standalone script.

## Usage

```
/generate-changelog
```

Or via CLI:
```bash
bash changelog.sh
```

## How It Works

1. Fetches all commits since the last git tag (or from a specified starting point)
2. Auto-categorizes commits into: **Added**, **Fixed**, **Changed**, **Removed**, **Security**
3. Uses conventional commit prefixes (feat:, fix:, chore:, docs:, refactor:, etc.) for categorization
4. Falls back to commit message analysis when no conventional prefix is found
5. Outputs a properly formatted `CHANGELOG.md` following Keep a Changelog 1.0.0 spec

## Categories

| Prefix | Category |
|--------|----------|
| `feat:` / `feature:` / `add:` / `new:` | Added |
| `fix:` / `bugfix:` / `patch:` / `hotfix:` | Fixed |
| `refactor:` / `perf:` / `optimize:` / `improve:` | Changed |
| `remove:` / `delete:` / `deprecate:` / `drop:` | Removed |
| `security:` / `sec:` | Security |

## Output Format

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- New feature description

### Fixed
- Bug fix description
```

## Script

The `changelog.sh` script:
- Accepts optional `--since-tag <tag>` argument
- Accepts optional `--output <file>` argument (default: CHANGELOG.md)
- Non-zero exit code on failure

## Example

```bash
# Generate changelog from last tag
bash changelog.sh

# Generate from specific tag
bash changelog.sh --since-tag v1.2.0

# Output to custom file
bash changelog.sh --output HISTORY.md
```
