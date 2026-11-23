# Git Changelog Generator

Automatically generates a structured, Keep-a-Changelog compliant `CHANGELOG.md` from git commit history since the latest release tag.

## 💰 Solves Bounty: $50 — [Opire Issue #1](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1)

---

## ⚡ Setup & Usage in 3 Steps

### Step 1: Clone or Copy Skill
```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
cd claude-builders-bounty
```

### Step 2: Run the Generator
Run using either the native skill, bash wrapper, or python:
```bash
bash skills/generate-changelog/changelog.sh
```
*(Or via Claude Code skill command: `/generate-changelog`)*

### Step 3: Inspect Output
Your formatted `CHANGELOG.md` will be created in your root directory.

---

## 📋 Sample Output Generated
```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-11-23

### Added
- feat(hook): add pre-tool-use destructive command blocker (`3fba40c`)
- feat(skill): add changelog generation skill (`9a1bc42`)

### Fixed
- fix(regex): align WHERE clause validation for delete (`8b3cd11`)

### Changed
- chore: update documentation and examples (`7a2de90`)
```
