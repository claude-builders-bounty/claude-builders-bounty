# generate-changelog

Auto-generate a structured `CHANGELOG.md` from git history.
Categorizes commits into **Added / Fixed / Changed / Removed** using conventional commits with keyword fallback.

## Setup (3 steps)

```bash
# 1. Copy script to your project
cp changelog.sh /your/project/

# 2. Make executable
chmod +x changelog.sh

# 3. Run
bash changelog.sh
```

No dependencies. Pure bash. Works on macOS and Linux.

## Usage

```bash
bash changelog.sh                      # write CHANGELOG.md
bash changelog.sh --dry-run            # preview only
bash changelog.sh --since v1.2.0       # start from specific tag
bash changelog.sh --version v2.0.0     # set version label
```

## Claude Code (SKILL.md)

Add to your project's `.claude/skills/` folder and invoke via `/generate-changelog`.

## How it categorizes

| Category | Triggers |
|---|---|
| **Added** | `feat:`, `add:` prefix, or keywords: *add, new, create, implement* |
| **Fixed** | `fix:`, `bug:` prefix, or keywords: *fix, bug, patch, correct* |
| **Changed** | `refactor:`, `chore:`, `ci:`, `perf:`, `docs:`, `style:` |
| **Removed** | `revert:`, `remove:`, `delete:`, or keywords: *remove, drop* |

See `sample-output.md` for a real example with 40+ commits.
