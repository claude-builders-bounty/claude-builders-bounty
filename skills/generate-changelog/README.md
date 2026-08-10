# Generate Changelog

A Claude Code skill and bash script that generates a structured `CHANGELOG.md` from git history — no dependencies beyond `git` and `bash`.

## Setup (3 Steps)

1. **Copy** the `skills/generate-changelog/` folder into your project
2. **Make the script executable**: `chmod +x skills/generate-changelog/changelog.sh`
3. **Run it**: `bash skills/generate-changelog/changelog.sh`

That's it. The script auto-detects your last git tag and categorizes commits.

## Usage

### Bash

```bash
# Default: writes CHANGELOG.md to the current directory
bash skills/generate-changelog/changelog.sh

# Custom output path
bash skills/generate-changelog/changelog.sh --output docs/CHANGELOG.md

# Start from a specific tag
bash skills/generate-changelog/changelog.sh --since v1.2.0

# Full history (ignore tags)
bash skills/generate-changelog/changelog.sh --all
```

### Claude Code

Place `SKILL.md` in your `.claude/skills/generate-changelog/` directory, then invoke `/generate-changelog` in Claude Code.

## How It Works

- Finds the latest git tag (or uses all commits if no tags exist)
- Scans commits with `git log --no-merges`
- Categorizes by conventional commit prefix into **Added** / **Fixed** / **Changed** / **Removed**
- Unrecognized prefixes default to **Changed**
- Outputs a markdown file with short commit hashes for traceability

## Supported Commit Prefixes

| Prefix | Category |
|--------|----------|
| `feat:`, `add:`, `new:`, `introduce:`, `implement:`, `support:`, `create:` | Added |
| `fix:`, `bug:`, `bugfix:`, `hotfix:`, `patch:`, `correct:`, `resolve:`, `repair:` | Fixed |
| `remove:`, `delete:`, `drop:`, `deprecate:` | Removed |
| `refactor:`, `chore:`, `ci:`, `build:`, `style:`, `perf:`, `docs:`, `test:`, `update:`, `change:`, `improve:`, `bump:`, `migrate:`, `rename:`, `revert:`, `config:`, `security:` | Changed |
| _(none)_ | Changed (default) |

Scopes (`feat(api):`) and breaking changes (`feat!:`) are supported.

## Requirements

- Git repository with commit history
- Bash 4+ (Git Bash on Windows works)

## Testing

Run the automated acceptance tests:

```bash
bash skills/generate-changelog/test/test_changelog.sh
```