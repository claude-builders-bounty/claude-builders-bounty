# changelog.sh

Generate a structured `CHANGELOG.md` from your git history.

## Setup

1. Copy `changelog.sh` to your project root (or anywhere in your repo)
2. `chmod +x changelog.sh`
3. Run it: `bash changelog.sh`

## Usage

```bash
# Default: changelog from latest tag to HEAD
bash changelog.sh

# From a specific tag
bash changelog.sh --tag v1.0.0

# From a specific date
bash changelog.sh --since "2025-01-01"

# All commits (no range)
bash changelog.sh --all

# Custom output file
bash changelog.sh --output RELEASE_NOTES.md
```

## How It Works

1. Reads git log for commits in the specified range
2. Categorizes each commit by its prefix:
   - **Added** — `add`, `feat`, `new`, `implement`, `create`, `support`
   - **Fixed** — `fix`, `bug`, `patch`, `resolve`, `correct`
   - **Changed** — `change`, `update`, `refactor`, `improve`, `enhance`, `bump`
   - **Removed** — `remove`, `delete`, `drop`, `deprecate`, `clean`
   - **Other** — anything else
3. Outputs a formatted `CHANGELOG.md` with commit hashes and dates

## Sample Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

Generated on 2026-04-15.

---

## [v0.0.1 → 065d473] (2026-04-15)

### Added

- feat: Add pre-tool-use hook to block destructive bash commands (065d473, 2026-04-06)
- feat: initial README with bounty board (1aeae2a, 2026-03-27)

### Other

- Initial commit (a80a580, 2026-03-27)
```

## Requirements

- `git` installed
- A git repository with at least one commit

No other dependencies needed.
