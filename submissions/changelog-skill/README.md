# CHANGELOG Generator

A Claude Code skill and standalone bash script that generates a well-formatted `CHANGELOG.md` from your git history, following the [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) specification.

## Features

- Parses **conventional commits** (`feat:`, `fix:`, `refactor:`, etc.) and maps them to changelog categories
- Falls back to **keyword analysis** for non-conventional commit messages
- Detects **breaking changes** from `BREAKING CHANGE:` in commit bodies or `!` in prefixes
- Preserves existing changelog entries when regenerating
- Filters out merge commits automatically
- Handles edge cases: no tags, no commits, empty repos

## Setup (Claude Code Skill)

1. Copy `SKILL.md` into your project's `.claude/skills/` directory (create it if needed):
   ```bash
   mkdir -p .claude/skills && cp SKILL.md .claude/skills/generate-changelog.md
   ```
2. Start Claude Code in your repository:
   ```bash
   claude
   ```
3. Run the skill:
   ```
   /generate-changelog
   ```

## Setup (Bash Script)

1. Copy `changelog.sh` to your repository root
2. Make it executable: `chmod +x changelog.sh`
3. Run it: `./changelog.sh`

### Bash script options

```
./changelog.sh                      # Generate CHANGELOG.md
./changelog.sh --version 2.1.0      # Use a specific version instead of "Unreleased"
./changelog.sh --stdout              # Print to stdout (don't write file)
./changelog.sh --output HISTORY.md   # Write to a different filename
```

## How it works

### Commit categorization

Commits are sorted into four categories from [Keep a Changelog](https://keepachangelog.com/en/1.1.0/):

| Category | Conventional prefixes | Keyword triggers |
|----------|----------------------|-----------------|
| **Added** | `feat:` | add, new, create, introduce, implement, support |
| **Fixed** | `fix:` | fix, bug, patch, resolve, close, correct, repair |
| **Changed** | `refactor:`, `perf:`, `style:`, `build:`, `ci:`, `chore:`, `docs:`, `test:` | update, change, improve, bump, migrate, rename, move |
| **Removed** | `revert:` | remove, delete, drop, deprecate, strip, clean up |

### Version range

The tool automatically detects the latest git tag and only includes commits since that tag. If no tags exist, the full commit history is used.

### Output format

The generated `CHANGELOG.md` follows keepachangelog.com format exactly:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2026-03-27

### Added
- Implement user authentication
- Support dark mode

### Fixed
- Correct off-by-one error in pagination

### Changed
- Update dependencies to latest versions
```

## Sample output

See [SAMPLE_OUTPUT.md](SAMPLE_OUTPUT.md) for a realistic example generated from a real repository.

## Requirements

- **Bash script:** Git, Bash 3.2+ (macOS default works), standard Unix tools (`sed`, `sort`, `date`)
- **Claude Code skill:** Claude Code CLI with skill support

## License

MIT
