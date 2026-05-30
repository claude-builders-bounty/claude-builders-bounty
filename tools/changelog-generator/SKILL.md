# Skill: Generate Changelog

Generate a structured `CHANGELOG.md` from git commit history, following [Keep a Changelog](https://keepachangelog.com/) format.

## Trigger

```
/generate-changelog
```

## What It Does

Parses git log since the last tag (or a specified ref), auto-categorizes each commit into semantic categories, and writes a formatted `CHANGELOG.md`.

## Categories

| Category | Pattern Match | Examples |
|----------|--------------|---------|
| **Added** | feat, add, new, introduce, implement | "feat: add user profile page" |
| **Fixed** | fix, bug, patch, hotfix, resolve, issue | "fix: resolve login timeout" |
| **Changed** | change, update, modify, refactor, improve, optimize | "refactor: simplify auth flow" |
| **Removed** | remove, delete, drop, deprecate, cleanup | "remove: delete deprecated endpoint" |
| **Security** | security, cve, vuln, auth, permission, xss, injection | "security: sanitize user input" |
| **Deprecated** | deprecat, legacy, obsolete | "deprecate: old API version" |
| **Other** | (fallback) | Everything else |

## Usage

### Via Script

```bash
chmod +x changelog.sh
./changelog.sh                          # Since last tag
./changelog.sh v1.0.0                   # Since specific tag
./changelog.sh v1.0.0 v2.0.0            # Custom version label
./changelog.sh v1.0.0 v2.0.0 CHANGELOG.md  # Custom output file
```

### Via Claude Code

```
/generate-changelog
```

This will:
1. Run `git describe --tags --abbrev=0` to find the last tag
2. Parse all commits since that tag with `git log`
3. Categorize each commit by message keywords
4. Write `CHANGELOG.md` with proper formatting

## Output Format

```markdown
# Changelog

## [v2.0.0] - 2026-05-30

### Added
- feat: add user profile page (`a1b2c3d`)
- implement OAuth2 login flow (`e5f6g7h`)

### Fixed
- fix: resolve login timeout on slow networks (`i9j0k1l`)
- patch: correct timezone handling in date picker (`m2n3o4p`)

### Changed
- refactor: simplify authentication middleware (`q5r6s7t`)
- update: upgrade dependencies to latest versions (`u8v9w0x`)

### Removed
- remove: delete deprecated REST API v1 (`y1z2a3b`)

### Security
- security: sanitize user input in search field (`c4d5e6f`)
```

## Conventional Commits Support

The script recognizes [Conventional Commits](https://www.conventionalcommits.org/) format:

```
type(scope): description

Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert
```

Scope is extracted and displayed in brackets when present:
- `feat(auth): add OAuth2` → `- feat: add OAuth2 ([auth]) (\`abc1234\`)`

## Implementation Notes

- **Zero dependencies** — pure bash + git
- **Works with any Git repository** — no language-specific logic
- **Idempotent** — running multiple times produces the same output for the same commit range
- **Commit hash links** — each entry includes the short SHA for traceability
- **Stats footer** — HTML comment with total commit count for machine parsing
