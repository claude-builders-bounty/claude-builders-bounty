# Changelog Generator Skill 📝

**Bounty #1 — $50**

A Claude Code skill + bash script that generates structured `CHANGELOG.md` from git history.

## What's Included

| File | Purpose |
|------|---------|
| `SKILL.md` | Claude Code skill definition — drop into your project |
| `changelog.sh` | Standalone bash script — works without Claude |

## Install

### As a Claude Code Skill
Copy `SKILL.md` to your project's `.claude/skills/` directory:
```bash
mkdir -p .claude/skills
cp SKILL.md .claude/skills/changelog-generator.md
```

Then use: `/generate-changelog`

### As a Standalone Script
```bash
cp changelog.sh /usr/local/bin/generate-changelog
generate-changelog              # Creates CHANGELOG.md
generate-changelog HISTORY.md   # Custom output path
```

## Features

- ✅ Categorizes commits: Added, Fixed, Changed, Removed, etc.
- ✅ Groups by git tags (semver) when available
- ✅ Unreleased section for commits after latest tag
- ✅ Commit short hashes for traceability
- ✅ Handles conventional commit prefixes
- ✅ Skips merge commits by default
- ✅ Works with zero-config on any git repo
- ✅ Both SKILL.md (Claude) and standalone bash script

## Commit Type Mapping

| Prefix | Section |
|--------|---------|
| `feat:`, `feature:` | Added |
| `fix:`, `bugfix:` | Fixed |
| `refactor:`, `change:`, `perf:`, `improve:` | Changed |
| `remove:`, `delete:` | Removed |
| `docs:`, `doc:` | Documentation |
| `test:`, `tests:` | Tests |
| `chore:`, `ci:`, `build:`, `deps:` | Maintenance |

## Example Output

```markdown
# Changelog

## [Unreleased]

### Added
- user authentication system (`a1b2c3d`)
- dashboard analytics page (`e4f5g6h`)

### Fixed
- resolve memory leak in worker pool (`i7j8k9l`)

## [v2.0.0] - 2026-03-15

### Added
- complete API redesign (`m0n1o2p`)
```

## Requirements

- Git repository with commit history
- Bash 4+ (for the script)
- No external dependencies

## License

MIT
