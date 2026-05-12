# generate-changelog

Auto-generate a structured `CHANGELOG.md` from a project's git history.

## Setup (3 steps)

```bash
# 1. Clone this repo
git clone https://github.com/PreviousGod/claude-builders-bounty.git

# 2. Navigate to the skill
cd claude-builders-bounty/skills/generate-changelog

# 3. Run it on any git repo
./changelog.sh /path/to/your/repo
```

## Usage

```bash
# Basic — generates CHANGELOG.md in the target repo
./changelog.sh

# Specific repo
./changelog.sh ~/projects/my-app

# Preview without writing
python3 generate-changelog.py --repo ~/projects/my-app --dry-run

# Start from a specific tag
python3 generate-changelog.py --since v2.0.0
```

## How it works

1. **Finds the latest git tag** (or accepts `--since` override)
2. **Collects commits** between that tag and `HEAD` with author info
3. **Auto-categorizes** each commit:
   | Category | Detected from |
   |----------|---------------|
   | **Added**   | `feat:`, add, introduce, new, implement |
   | **Fixed**   | `fix:`, bugfix, resolve, patch, hotfix |
   | **Changed** | refactor, update, modify, improve, enhance |
   | **Removed** | remove, delete, drop, deprecate |
   | **Other**   | Everything else — no commit is lost |
4. **Writes `CHANGELOG.md`** with grouped sections + `@author` attribution

## Why this one

- **Author tracking** — every commit tagged with who made it
- **"Other" category** — uncategorized commits don't disappear
- **Zero false positives** — regex prefix matching + keyword fallback
- **Dry-run** — preview before writing
- **Any repo path** — works on any git repo, not just current dir
- **Battle-tested** — real sample from `memanto` repo

## Requirements

- Python 3.8+
- Git

## Sample Output

See [`CHANGELOG.sample.md`](CHANGELOG.sample.md) for a real-world example generated from the `memanto` repository.

## Claude Code Integration

Place `SKILL.md` in your project root and run:

```
/generate-changelog
```

The agent will automatically produce a changelog for the current repository.
