# Structured CHANGELOG Generator

A Claude Code skill and CLI utility that automatically parses git history since the latest release tag and produces a categorized, standard [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) markdown file.

**Fulfills Bounty #1 ($50) — Powered by Opire.**

---

## ⚡ Quick Setup (3 Steps or Fewer)

1. Clone or copy the script to your repository root:
   ```bash
   curl -O https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/changelog.py
   ```
2. Generate your changelog:
   ```bash
   python changelog.py
   # or
   bash changelog.sh
   ```
3. Use via Claude Code skill:
   Copy `skills/generate-changelog/` to `~/.claude/skills/` to enable `/generate-changelog`.

---

## 📋 Features & Acceptance Criteria

- ✅ **Tag Aware**: Detects latest git tag (`git describe --tags --abbrev=0`) or falls back to recent history.
- ✅ **Auto-Categorization**: Automatically categorizes commits into:
  - `Added` (`feat:`, `add:`, etc.)
  - `Fixed` (`fix:`, `bug:`, etc.)
  - `Changed` (`refactor:`, `perf:`, `chore:`, etc.)
  - `Removed` (`deprecate:`, `remove:`, `delete:`, etc.)
- ✅ **Standard Format**: Outputs valid Keep-a-Changelog Markdown with commit hash links.
