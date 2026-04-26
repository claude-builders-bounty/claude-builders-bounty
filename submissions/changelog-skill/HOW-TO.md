# How-To Guide: Generate Structured CHANGELOG from Git History

A step-by-step walkthrough for using this skill in real projects.

---

## Quick Start (30 seconds)

```bash
# Download the script into your project
curl -O https://raw.githubusercontent.com/xamdkx/claude-builders-bounty/bounty/1-changelog-skill/submissions/changelog-skill/generate-changelog.sh

# Run it
bash generate-changelog.sh
```

Your `CHANGELOG.md` is ready. That's it.

---

## Step-by-Step Guide

### Step 1: Check your git tags

The script auto-detects your last git tag to determine the range:

```bash
git tag --list
```

If you see tags like `v1.0.0`, `v1.1.0`, the script will generate a changelog since the latest tag.

If you have **no tags**, it generates the full history automatically.

### Step 2: Run the script

**Option A — Since last tag (most common):**
```bash
bash generate-changelog.sh
```

**Option B — Since a specific version:**
```bash
bash generate-changelog.sh v1.0.0
```

**Option C — Between two versions (for release notes):**
```bash
bash generate-changelog.sh v1.0.0 v2.0.0
```

**Option D — Full project history:**
```bash
bash generate-changelog.sh --all
```

### Step 3: Review the output

Open `CHANGELOG.md` in your editor. You'll see:

```markdown
# Changelog

## [Since v1.2.0] — 2026-04-15

### Added
- feat: add dark mode toggle (`a1b2c3d` by alice, 2026-04-14)

### Fixed
- fix: resolve login timeout (`d4e5f6g` by bob, 2026-04-13)

### Changed
- refactor: simplify API routes (`h7i8j9k` by alice, 2026-04-12)
```

### Step 4: Include in your release

```bash
# Add to git
git add CHANGELOG.md
git commit -m "docs: update CHANGELOG for v1.3.0"
git tag v1.3.0
git push origin main --tags
```

---

## Tips for Better Changelogs

### Use Conventional Commits

The script auto-categorizes when you use prefixes:

| Prefix | Category | Example |
|--------|----------|---------|
| `feat:` | Added | `feat: add export button` |
| `fix:` | Fixed | `fix: resolve null pointer` |
| `refactor:` | Changed | `refactor: simplify auth flow` |
| `perf:` | Performance | `perf: cache API responses` |
| `security:` | Security | `security: patch XSS in comments` |

Even without prefixes, keywords like "add", "fix", "remove", "update" are detected.

### Automate with CI/CD

Add to your GitHub Actions workflow:

```yaml
# .github/workflows/changelog.yml
name: Generate Changelog
on:
  push:
    tags: ['v*']
jobs:
  changelog:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for tags
      - run: bash generate-changelog.sh
      - uses: actions/upload-artifact@v4
        with:
          name: changelog
          path: CHANGELOG.md
```

### Use with Claude Code

If you have the `SKILL.md` installed:

```
/generate-changelog
```

Claude will run it and show you the output directly.

---

## Troubleshooting

**"No commits found"**
- Make sure you're in a git repository (`git status`)
- Check if the tag exists (`git tag --list`)

**"Wrong categories"**
- Use Conventional Commits prefixes for best results
- The script falls back to keyword detection for plain messages

**"Missing commits"**
- By default, only shows commits since last tag
- Use `--all` for full history
- Merge commits are skipped by design (they're noise)

---

## How It Works (Technical)

1. `git log --pretty=format:"%H|||%s|||%an|||%ad"` extracts commits
2. Each commit message is matched against regex patterns:
   - First checks Conventional Commits prefixes (`^feat`, `^fix`, etc.)
   - Falls back to keyword detection (`added`, `fixed`, `removed`, etc.)
3. Commits are grouped into categories
4. Output follows [Keep a Changelog](https://keepachangelog.com/) format
5. Footer includes commit count and unique contributor count
