# Claude Code Structured CHANGELOG Generator Skill 📝

> A Claude Code skill (`SKILL.md`) and CLI script that automatically generates a structured `CHANGELOG.md` from git commits since the last release tag.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Bounty Issue #1](https://img.shields.io/badge/Bounty-%2450%20USDC-green.svg)](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1)

---

## ⚡ Setup & Usage in 3 Steps or Fewer

### Step 1: Clone or Copy into Your Project
```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
cd claude-builders-bounty
```

### Step 2: Run the Generator
```bash
./skills/generate-changelog/changelog.sh --version "v1.2.0"
```

### Step 3 (Optional): Use as Claude Code Skill
Place `SKILL.md` inside `~/.claude/skills/generate-changelog/SKILL.md` to run `/generate-changelog` directly in Claude Code.

---

## 🔍 Features
- **Git Tag Aware:** Automatically scopes commits since `git describe --tags --abbrev=0`.
- **Keep a Changelog Formatting:** Generates `### Added`, `### Fixed`, `### Changed`, and `### Removed` categories based on Conventional Commits.
- **Commit Links:** Formats commit hashes into clickable links.
- **Sample Output:** See [`sample_outputs/SAMPLE_CHANGELOG.md`](sample_outputs/SAMPLE_CHANGELOG.md).

---

## 📄 License
MIT License. Built for the Claude Code Builders Community.
