# changelog-from-git — Claude Code Skill

Generate a structured `CHANGELOG.md` from git history. Parses
[Conventional Commits](https://www.conventionalcommits.org/), buckets them by
semver tag, and emits [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
formatted Markdown — breaking changes flagged, noise filtered out.

## Install

```bash
mkdir -p ~/.claude/skills/changelog-from-git
curl -fsSL https://raw.githubusercontent.com/Ishant5436/claude-builders-bounty/main/submissions/bounty-1-ishant/SKILL.md \
  -o ~/.claude/skills/changelog-from-git/SKILL.md
curl -fsSL https://raw.githubusercontent.com/Ishant5436/claude-builders-bounty/main/submissions/bounty-1-ishant/changelog_gen.py \
  -o ~/.claude/skills/changelog-from-git/changelog_gen.py
```

Claude Code auto-discovers the skill on next launch.

## Quick start

```bash
# Preview the next release (everything since the latest tag)
python3 ~/.claude/skills/changelog-from-git/changelog_gen.py --repo . --unreleased-only

# Write the full changelog
python3 ~/.claude/skills/changelog-from-git/changelog_gen.py --repo . --output CHANGELOG.md
```

## Example

Given these commits on top of tag `v1.0.0`:

```
feat: add login page
fix(auth): session cookie not cleared on logout   <- tagged v1.0.0
perf: cache user lookups
feat!: drop Node 16 support
```

The skill produces:

```markdown
## [Unreleased]

### ⚠ BREAKING CHANGES

- drop Node 16 support (`d3e8be0`)

### Added

- drop Node 16 support (`d3e8be0`)

### Changed

- cache user lookups (`13b6832`)

## [v1.0.0] - 2026-06-04

### Added

- add login page (`ae7058a`)

### Fixed

- **auth:** session cookie not cleared on logout (`d0b33bb`)
```

## Type mapping

| Commit type | CHANGELOG section |
|---|---|
| `feat`, `feature`, `add` | Added |
| `fix`, `bugfix` | Fixed |
| `perf`, `refactor`, `revert`, `change` | Changed |
| `deprecate` | Deprecated |
| `remove` | Removed |
| `security`, `sec` | Security |
| other | Changed |

`feat!:` or a `BREAKING CHANGE:` footer is surfaced under **⚠ BREAKING CHANGES**.
`chore`, `ci`, `build`, `test`, `style`, and `docs` are dropped by default
(`--include-all` keeps them).

## Requirements

- Python 3.8+
- `git` on PATH
- No third-party packages

## License

MIT
