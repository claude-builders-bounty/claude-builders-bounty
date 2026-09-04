# Changelog Generator Skill

## Description
Automatically generates a structured `CHANGELOG.md` from a project's git history since the last tag.

## Usage

### Via CLI
```bash
bash skills/changelog-generator/changelog.sh
```

### With custom options
```bash
# Custom range
bash skills/changelog-generator/changelog.sh --from v1.0.0 --to HEAD

# Output to file
bash skills/changelog-generator/changelog.sh -o CHANGELOG.md

# Dry run (stdout only)
bash skills/changelog-generator/changelog.sh --dry-run
```

### As Claude Code Command
Add to your project's `CLAUDE.md`:
```
/generate-changelog — Run bash skills/changelog-generator/changelog.sh to update CHANGELOG.md
```

## How It Works

1. **Finds the last git tag** (or uses `--from` if specified)
2. **Fetches all commits** since that tag
3. **Auto-categorizes** each commit by keyword:
   - **Added** — `add`, `create`, `new`, `implement`, `introduce`
   - **Fixed** — `fix`, `bug`, `patch`, `resolve`, `hotfix`
   - **Changed** — `update`, `modify`, `refactor`, `improve`, `optimize`
   - **Removed** — `remove`, `delete`, `deprecate`, `drop`
   - **Security** — `security`, `cve`, `vulnerability`, `auth`
   - **Docs** — `doc`, `readme`, `comment`, `typo`
4. **Generates** a Keep-a-Changelog formatted `CHANGELOG.md`
5. **Creates a new git tag** for version tracking (optional)

## Output Format

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- New user authentication system (#123)
- OAuth2 support for GitHub login (#124)

### Fixed
- Memory leak in background worker (#120)
- Race condition in order processing (#121)

### Changed
- Upgrade Express from 4.x to 5.x (#118)
- Migrate database queries to use prepared statements (#119)

### Removed
- Deprecated legacy API endpoints (#115)

## [1.0.0] - 2026-01-15

### Added
- Initial release
```

## Setup (3 steps)

1. **Copy this skill** into your project's `.claude/skills/` or `skills/` directory
2. **Make the script executable**: `chmod +x skills/changelog-generator/changelog.sh`
3. **Run it**: `bash skills/changelog-generator/changelog.sh`

## Dependencies

- `git` (>= 2.0)
- Standard Unix tools: `grep`, `sed`, `awk`, `date`
- No npm/pip required — pure bash

## Sample Output

See `skills/changelog-generator/CHANGELOG.sample.md` for example output generated from real repos.
