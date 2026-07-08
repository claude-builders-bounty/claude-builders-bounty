# Issue 1 Generate Changelog Skill

This submission provides a native Claude Code skill plus a bash wrapper for generating `CHANGELOG.md` from git history.

## Setup

```bash
cd submissions/issue-1-generate-changelog-skill
bash changelog.sh
```

The command writes `CHANGELOG.md` in the target repository.

## Usage

```bash
bash changelog.sh --repo /path/to/repo
```

The script finds the latest git tag, reads commits since that tag, categorizes them into `Added`, `Fixed`, `Changed`, and `Removed`, and writes a formatted changelog.
