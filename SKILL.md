# Generate CHANGELOG from Git History

Generates a structured `CHANGELOG.md` by scanning commits since the last git tag,
auto-categorizing them into Added / Fixed / Changed / Removed sections.

## Usage

```
/generate-changelog
```

Or run directly:

```bash
bash changelog.sh
# With options:
bash changelog.sh --since v1.2.0 --output CHANGELOG.md
```

## What it does

1. Finds the last git tag (or uses full history if none exists)
2. Collects all commits since that tag (excluding merge commits)
3. Categorizes each commit:
   - **Added** — `feat:`, `add:`, `new:`, or messages starting with "implement/create"
   - **Fixed** — `fix:`, `bug:`, `hotfix:`, or messages starting with "fix/resolve/closes"
   - **Removed** — `remove:`, `delete:`, `drop:`, `deprecate:`
   - **Changed** — `chore:`, `refactor:`, `perf:`, `style:`, `docs:`, `ci:`, `build:`, or "update/improve/bump/upgrade"
   - **Other** — anything that doesn't match the above
4. Writes a `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/) format
   with commit hash links to the remote repository

## Setup (3 steps)

1. Download `changelog.sh` into your project root
2. Make it executable: `chmod +x changelog.sh`
3. Run it: `./changelog.sh`

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `--since <tag\|commit>` | last git tag | Custom starting point |
| `--output <file>` | `CHANGELOG.md` | Output file path |

## Requirements

- `git` in PATH
- Bash 4+ (macOS: `brew install bash`)
