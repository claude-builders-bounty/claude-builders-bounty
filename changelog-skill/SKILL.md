# Changelog Generator Skill

Generate a structured `CHANGELOG.md` from a project's git history.

## Usage

### As a Claude Code Skill

Use `/generate-changelog` in Claude Code, and I will:
1. Find the last git tag in the repository
2. Extract all commits since that tag
3. Categorize them by conventional commit prefix
4. Generate a formatted `CHANGELOG.md`

### As a Bash Script

```bash
bash changelog.sh                    # Output to CHANGELOG.md
bash changelog.sh RELEASE_NOTES.md   # Output to custom file
```

## Categorization Rules

| Commit Prefix | Category |
|---------------|----------|
| `feat:` | Added |
| `fix:` | Fixed |
| `refactor:`, `perf:`, `style:`, `docs:`, `chore:`, `build:`, `ci:`, `test:` | Changed |
| `remove:`, `delete:`, `deprecate:` | Removed |
| (other) | Changed |

Scopes like `feat(auth):` are supported.

## Example Output

```markdown
# Changelog

## [Unreleased] — 2026-05-28 (since v1.2.0)

### Added
- feat: add user authentication (a1b2c3d)
- feat(api): add rate limiting (e4f5g6h)

### Fixed
- fix: resolve null pointer in login (i7j8k9l)
- fix(db): connection pool leak (m0n1o2p)

### Changed
- docs: update API documentation (q3r4s5t)
- refactor: extract auth middleware (u6v7w8x)

### Removed
- remove: deprecated legacy endpoint (y9z0a1b)
```

## Setup (3 steps)

1. Clone or download `changelog.sh`
2. Make it executable: `chmod +x changelog.sh`
3. Run it in any git repository: `bash changelog.sh`

## Requirements

- Git repository with at least one commit
- Bash 4+ (for associative arrays)
- `git` command available
