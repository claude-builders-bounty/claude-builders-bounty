# Generate Structured CHANGELOG

This skill generates a structured `CHANGELOG.md` from a project's git history, automatically categorizing commits into `Added`, `Fixed`, `Changed`, and `Removed` sections.

## Usage

Run `/generate-changelog` in Claude Code, or execute the standalone script:

```bash
bash skills/generate-changelog/changelog.sh
```

### Options

| Flag | Description | Default |
|------|-------------|---------|
| `--since-tag <tag>` | Generate changelog from commits after this tag | Last git tag |
| `--output <file>` | Output file path | `CHANGELOG.md` |
| `--repo <path>` | Path to git repository | Current directory |
| `--dry-run` | Print to stdout instead of writing a file | Off |

## How It Works

1. Finds the most recent git tag (or uses `--since-tag`)
2. Collects all commits between that tag and `HEAD`
3. Parses each commit message and categorizes by prefix or keyword:
   - **Added**: `feat:`, `add:`, new features
   - **Fixed**: `fix:`, `bugfix:`, `hotfix:`, bug corrections
   - **Changed**: `refactor:`, `update:`, `change:`, modifications
   - **Removed**: `remove:`, `delete:`, deletions
4. Groups uncategorized commits into a `Other` section
5. Outputs a properly formatted `CHANGELOG.md` in [Keep a Changelog](https://keepachangelog.com/) format

## Commit Convention

The categorizer follows [Conventional Commits](https://www.conventionalcommits.org/) by default:

```
feat: add user authentication         → Added
fix: resolve login timeout issue      → Fixed
refactor: simplify DB connection pool → Changed
remove: delete deprecated API v1      → Removed
```

Commits without a conventional prefix are categorized by keyword detection:

- Keywords like "add", "new", "create", "introduce" → **Added**
- Keywords like "fix", "resolve", "repair", "patch" → **Fixed**
- Keywords like "update", "change", "modify", "improve" → **Changed**
- Keywords like "remove", "delete", "drop", "deprecate" → **Removed**

## Output Format

```markdown
# Changelog

## [Unreleased]

### Added
- feat: add user authentication (#42)
- new dashboard analytics endpoint

### Fixed
- fix: resolve login timeout issue (#39)
- patch memory leak in worker process

### Changed
- refactor: simplify DB connection pool
- update dependency versions

### Removed
- remove: delete deprecated API v1

### Other
- misc: update CI pipeline config
```

## Setup (3 steps)

1. **Copy** the `skills/generate-changelog/` folder into your project
2. **Run** `bash skills/generate-changelog/changelog.sh` to generate your first changelog
3. **Commit** the generated `CHANGELOG.md` to your repository

## Requirements

- Git (version 2.0+)
- Bash (version 3.2+)

No additional dependencies required.
