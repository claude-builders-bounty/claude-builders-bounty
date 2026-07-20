---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the last tag. Auto-categorizes commits into Added, Fixed, Changed, and Removed sections using conventional commit prefixes and keyword analysis.
---

# Generate Changelog Skill

You are a changelog generator. Your task is to produce a well-formatted `CHANGELOG.md` from a project's git history.

## Instructions

Follow these steps precisely:

### Step 1 — Find the baseline

```bash
# Get the most recent tag (baseline for changes)
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -z "$LAST_TAG" ]; then
  echo "No tags found. Using entire git history."
  LOG_RANGE="HEAD"
else
  echo "Generating changelog since tag: $LAST_TAG"
  LOG_RANGE="${LAST_TAG}..HEAD"
fi
```

### Step 2 — Collect commits

```bash
# Get commits with hash, author, and message
git log $LOG_RANGE --pretty=format:"%H|%an|%s" --no-merges
```

### Step 3 — Categorize each commit

Use these rules to classify commits:

| Category | Prefixes / Keywords |
|----------|-------------------|
| **Added** | `feat:`, `feat(`, `add:`, `new:`, `feature:` |
| **Fixed** | `fix:`, `fix(`, `bug:`, `bugfix:`, `hotfix:`, `patch:` |
| **Changed** | `refactor:`, `refactor(`, `chore:`, `style:`, `perf:`, `perf(`, `improve:`, `update:`, `change:`, `docs:` |
| **Removed** | `remove:`, `remove(`, `delete:`, `drop:`, `deprecate:`, `revert:` |
| **Other** | Anything not matching above |

### Step 4 — Write CHANGELOG.md

Write the file in this exact format:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] — {TODAY_DATE}

> Changes since `{LAST_TAG}` ({N} commits)

### ✨ Added
- {commit message} ([`{short_hash}`]({repo_url}/commit/{full_hash})) — _{author}_

### 🐛 Fixed
- {commit message} ([`{short_hash}`]({repo_url}/commit/{full_hash})) — _{author}_

### 🔄 Changed
- {commit message} ([`{short_hash}`]({repo_url}/commit/{full_hash})) — _{author}_

### 🗑️ Removed
- {commit message} ([`{short_hash}`]({repo_url}/commit/{full_hash})) — _{author}_

### 📝 Other
- {commit message} ([`{short_hash}`]({repo_url}/commit/{full_hash})) — _{author}_
```

Only include sections that have commits. Skip empty sections.

### Step 5 — Confirm

Tell the user:
- Where `CHANGELOG.md` was written
- How many commits were processed
- How many fell into each category
- The tag range used (e.g., `v1.2.0..HEAD`)

## Important Notes

- Strip conventional commit prefixes from display messages (e.g., `feat: Add login` → `Add login`)
- If no tags exist, use "Initial Release" as the header
- Detect the remote URL with `git remote get-url origin` to build commit links
- If the repo URL cannot be determined, use relative links like `../../commit/{hash}`
- Run this in the root of any git repository
