# generate-changelog

A Python script + Claude Code skill that generates CHANGELOG.md from git history.

## Setup

**1.** Copy `changelog.py` and `changelog.sh` into your project.

**2.** Run:

```bash
bash changelog.sh -o CHANGELOG.md
```

**3.** (Optional) Install as a Claude Code skill:

```bash
cp SKILL.md .claude/skills/generate-changelog.md
```

## Options

```
--since, -s    Tag or date (default: last tag)
--until, -u    End date for range
--output, -o   Output file (default: stdout)
--version, -v  Version heading (default: Unreleased)
--repo, -r     Target repo path
--date, -d     Release date
```

## Requirements

Python 3.8+, Git 2.20+
