# Generate CHANGELOG

Generates a structured, human-readable CHANGELOG.md from git history.

## Usage

Run `/generate-changelog` in any git repository. Optionally specify a version:

```
/generate-changelog
/generate-changelog 2.1.0
/generate-changelog --since v1.0.0
```

## What it does

1. Reads git log since the last tag (or all history if no tags exist)
2. Groups commits by type: Features, Bug Fixes, Breaking Changes, Performance, Docs, Chores
3. Filters out noise (merge commits, version bumps, auto-generated commits)
4. Writes or prepends to `CHANGELOG.md` in Keep a Changelog format
5. Prints a summary of what was added

## Instructions

<command-instructions>
You are generating a CHANGELOG from git history. Follow these steps exactly:

### Step 1 — Get the version

If the user passed a version argument, use it. Otherwise:
- Run `git describe --tags --abbrev=0 2>/dev/null` to find the latest tag
- Run `git tag --sort=-version:refname | head -5` to see recent tags
- If no tags exist, use "Unreleased"
- The new version being documented is whatever the user specified, or "Unreleased"

### Step 2 — Collect commits

Run this command to get commits since the last tag:
```bash
git log $(git describe --tags --abbrev=0 2>/dev/null || echo "")..HEAD --pretty=format:"%H|%s|%an|%ad" --date=short 2>/dev/null || git log --pretty=format:"%H|%s|%an|%ad" --date=short
```

If `--since` was passed, use: `git log --since="<date>" --pretty=format:"%H|%s|%an|%ad" --date=short`

### Step 3 — Categorize commits

Group each commit into one of these categories based on the subject line:

| Category | Prefixes / keywords |
|----------|-------------------|
| ⚠️ Breaking Changes | `BREAKING`, `!:` after type, `breaking change` |
| ✨ Features | `feat`, `feature`, `add`, `new`, `implement` |
| 🐛 Bug Fixes | `fix`, `bug`, `patch`, `correct`, `resolve` |
| ⚡ Performance | `perf`, `optimize`, `speed`, `cache` |
| 📚 Documentation | `docs`, `doc`, `readme`, `changelog` |
| ♻️ Refactoring | `refactor`, `rework`, `restructure`, `clean` |
| 🧪 Tests | `test`, `spec`, `coverage` |
| 🔧 Chores | `chore`, `ci`, `build`, `deps`, `bump`, `version`, `release`, `merge` |

Skip: merge commits (`Merge branch`, `Merge pull request`), version bumps (`bump version`, `v\d+\.\d+`), auto-generated commits.

### Step 4 — Get the date

Run `date +%Y-%m-%d` for today's date.

### Step 5 — Write the CHANGELOG

Check if `CHANGELOG.md` already exists:
- If yes: prepend the new section after the `# Changelog` header
- If no: create from scratch

Format (Keep a Changelog):
```markdown
# Changelog

All notable changes to this project will be documented in this file.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)

## [VERSION] - YYYY-MM-DD

### ⚠️ Breaking Changes
- Description of breaking change ([abc1234](link))

### ✨ Features  
- Description of feature ([abc1234](link))

### 🐛 Bug Fixes
- Description of fix ([abc1234](link))

### ⚡ Performance
- Description of improvement ([abc1234](link))

### 📚 Documentation
- Description ([abc1234](link))

### ♻️ Refactoring
- Description ([abc1234](link))

### 🔧 Chores
- Description ([abc1234](link))
```

Rules:
- Only include categories that have commits
- Each entry: `- <clean description> ([<short-sha>](<repo-url>/commit/<full-sha>))`
- Clean the description: remove conventional commit prefix (`feat:`, `fix:` etc), capitalize first letter
- If no remote URL: use `([<short-sha>](...))` without a link
- Get remote URL with: `git remote get-url origin 2>/dev/null`
- Convert GitHub SSH URLs: `git@github.com:owner/repo.git` → `https://github.com/owner/repo`

### Step 6 — Report

Tell the user:
- How many commits were processed
- How many were included (excluding noise)
- Which sections were written
- The file path written to
</command-instructions>
