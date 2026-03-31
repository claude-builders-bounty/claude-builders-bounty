# generate-changelog

Generate a structured CHANGELOG.md from git history — as a Claude Code skill or a standalone bash script.

## Setup (3 steps)

### 1. Install

Copy the `skills/generate-changelog/` folder into your project:

```bash
cp -r skills/generate-changelog/ /path/to/your-project/.claude/skills/
```

Or, for the bash script only:

```bash
cp skills/generate-changelog/changelog.sh /path/to/your-project/
```

### 2. Run

**As a Claude Code skill:**

```
/generate-changelog
```

**As a bash script:**

```bash
bash changelog.sh                # writes CHANGELOG.md
bash changelog.sh CHANGES.md     # writes to custom filename
```

### 3. Review

Open the generated `CHANGELOG.md` and verify the categorization. Commit it to your repo.

## How It Works

- Finds the most recent git tag to determine the version boundary
- Fetches all commits since that tag (or all commits if no tags exist)
- Categorizes commits by their conventional commit prefix:
  - `feat`, `add`, `new` → **Added**
  - `fix`, `bugfix`, `patch` → **Fixed**
  - `refactor`, `update`, `improve`, `chore`, `docs`, `ci` → **Changed**
  - `remove`, `delete`, `revert` → **Removed**
- Outputs a [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) compliant file

## Requirements

- Git repository with at least one commit
- Bash 4+ (macOS, Linux, WSL)
- For the skill: Claude Code with skill support
