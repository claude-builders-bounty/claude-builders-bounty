# generate-changelog

Auto-generate a structured `CHANGELOG.md` from git history.

## Setup (3 steps)

```bash
# 1. Copy the script
cp changelog.sh /usr/local/bin/changelog.sh
chmod +x /usr/local/bin/changelog.sh

# 2. (Optional) Copy the Claude Code skill
cp SKILL.md ~/.claude/skills/generate-changelog.md

# 3. Run it
cd your-project && bash changelog.sh
```

## Usage

```bash
bash changelog.sh              # Commits since last git tag
bash changelog.sh v2.0.0       # Commits since specific tag
bash changelog.sh --all        # Full git history
```

Or in Claude Code: `/generate-changelog`

## How it works

1. Detects the latest git tag (or uses full history if none)
2. Fetches all non-merge commits since that tag
3. Auto-categorizes using conventional commit prefixes and keyword heuristics:
   - **Added**: `feat`, `add`, `new`, `create`, `implement`
   - **Fixed**: `fix`, `bug`, `patch`, `resolve`
   - **Changed**: `refactor`, `update`, `improve`, `chore`, `docs`, `perf`
   - **Removed**: `remove`, `delete`, `drop`, `deprecat`
4. Outputs a [Keep a Changelog](https://keepachangelog.com/) formatted `CHANGELOG.md`

## Sample output

See [SAMPLE_OUTPUT.md](./SAMPLE_OUTPUT.md) for a real example generated on this repository.

## Stack

Pure bash. No dependencies. Works on macOS and Linux.
