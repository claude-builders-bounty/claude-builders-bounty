# Changelog Generator

Automatically generates a structured `CHANGELOG.md` from your git history.

## Installation (3 steps)

1. **Clone the repo**
   ```bash
   git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
   cd claude-builders-bounty
   ```

2. **Make the scripts executable**
   ```bash
   chmod +x changelog.sh generate-changelog
   ```

3. **Run it**
   ```bash
   bash changelog.sh
   # or
   ./generate-changelog
   ```

## Usage

```bash
# Generate since the latest git tag
bash changelog.sh

# Generate since a specific tag
bash changelog.sh --since v1.0.0

# Custom output file
bash changelog.sh --output my-changelog.md

# Specify repo path
bash changelog.sh --repo-path /path/to/repo

# Python version
python generate-changelog
python generate-changelog --since v1.0.0 --output CHANGELOG.md
```

## How It Works

The script reads your git log, categorizes each commit by its prefix, and writes a structured `CHANGELOG.md`:

| Prefix | Category |
|--------|----------|
| `feat:`, `add:` | Added |
| `fix:`, `bug:` | Fixed |
| `change:`, `refactor:` | Changed |
| `remove:`, `drop:` | Removed |

## Example Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

> Generated since tag: `v0.1.0`

## Added

- feat: add user authentication system (a1b2c3d)
- add: initial project scaffold (e4f5g6h)

## Fixed

- fix: resolve memory leak in connection pool (i7j8k9l)

## Changed

- refactor: simplify API response formatting (m0n1o2p)

## Removed

- drop: legacy webhook endpoint (q3r4s5t)
```