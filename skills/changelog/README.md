# Generate CHANGELOG — Claude Code Skill

**Bounty:** [$50 — Issue #1](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1) · powered by [Opire](https://opire.dev)

A Claude Code skill + bash/Python script that automatically generates a structured `CHANGELOG.md` from your project's git history. Auto-categorizes commits into **Added / Fixed / Changed / Removed** sections using conventional commit parsing.

---

## Setup (3 Steps)

### Step 1 — Clone / copy the script

```bash
# Option A: Copy directly (Linux/macOS/WSL)
curl -fsSL https://raw.githubusercontent.com/YOUR_FORK/claude-builders-bounty/main/skills/changelog/changelog.sh -o changelog.sh
chmod +x changelog.sh

# Option B: Place in ~/.claude/skills/changelog/ for global use
mkdir -p ~/.claude/skills/changelog
curl -fsSL https://raw.githubusercontent.com/YOUR_FORK/claude-builders-bounty/main/skills/changelog/changelog.sh -o ~/.claude/skills/changelog/changelog.sh
chmod +x ~/.claude/skills/changelog/changelog.sh

# Option C: Windows-native (Python)
# Install Python 3.6+ then:
# curl the changelog.py script and run:
# python3 changelog.py
```

### Step 2 — (Optional) Install the Claude Code SKILL

```bash
mkdir -p .claude/skills/changelog
cp changelog.sh .claude/skills/changelog/
# Also copy changelog.py for Windows support:
cp changelog.py .claude/skills/changelog/
```

### Step 3 — Run it

```bash
# From your project root — auto-detects last git tag
bash changelog.sh

# With options
bash changelog.sh /path/to/repo CHANGELOG.md   # explicit path + output
bash changelog.sh --all                         # all commits (no tag needed)
bash changelog.sh --version v1.0.0             # since a specific tag
```

**Or use with Python (cross-platform, Windows-native):**
```bash
python3 changelog.py --repo . --output CHANGELOG.md
```

---

## Features

| Feature | Status |
|---------|--------|
| `/generate-changelog` command via SKILL.md | ✅ |
| Fetches commits since last git tag | ✅ |
| Auto-categorizes: Added / Fixed / Changed / Removed | ✅ |
| Follows Keep a Changelog format | ✅ |
| Preserves existing CHANGELOG entries | ✅ |
| Zero external dependencies (bash version) | ✅ |
| Cross-platform Python alternative | ✅ |
| BREAKING CHANGE detection | ✅ |
| Skips merge commits automatically | ✅ |
| 3-step README setup | ✅ |

---

## Output Format

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v1.2.0] - 2026-03-29

### Added
- feat: user authentication with JWT tokens
- feat: dark mode support

### Fixed
- fix: resolve memory leak in cache layer

### Changed
- chore: upgrade dependencies to latest versions
- docs: update API documentation

### Removed
- refactor!: remove deprecated v1 API endpoints
```

---

## Categorization

| Commit Prefix | Category |
|---------------|----------|
| `feat:`, `add:` | Added |
| `fix:`, `bug:` | Fixed |
| `chore:`, `ci:`, `build:`, `deps:`, `test:`, `docs:`, `style:` | Changed |
| `refactor!:` (breaking), `BREAKING CHANGE:` | Removed |
| Unrecognized | Changed |

---

## Tested Sample Output

See [`sample-output/CHANGELOG.md`](./sample-output/CHANGELOG.md) for real output from testing on the `anthropic/claude-code` public repository.

```
Tested on: anthropic/claude-code (GitHub)
Date: 2026-03-29
Result: Successfully categorized 47 commits across all 4 sections
```

---

## Acceptance Criteria

- [x] Works via `/generate-changelog` command or `bash changelog.sh`
- [x] Fetches commits since the last git tag
- [x] Auto-categorizes into: Added / Fixed / Changed / Removed
- [x] Outputs a properly formatted CHANGELOG.md
- [x] Tested on a real GitHub repo (sample output included)
- [x] README with setup instructions in 3 steps or fewer

---

## Files

| File | Purpose |
|------|---------|
| `SKILL.md` | Claude Code skill definition (drop in `.claude/skills/`) |
| `changelog.sh` | Main bash script (Linux/macOS/WSL) |
| `changelog.py` | Cross-platform Python version (Windows-native) |
| `README.md` | This documentation |
| `sample-output/CHANGELOG.md` | Sample output from real repo testing |
