# 📝 Generate Changelog Skill & Tool

Automatically generate clean, structured `CHANGELOG.md` files following the [Keep a Changelog](https://keepachangelog.com/) standard directly from your project's git commit history.

---

## ⚡ 3-Step Setup

1. **Copy the tool into your project:**
   ```bash
   cp skills/generate-changelog/changelog.sh ./changelog.sh && chmod +x ./changelog.sh
   ```

2. **Generate your changelog:**
   ```bash
   ./changelog.sh --write
   ```

3. **(Optional) Enable Claude Code Slash Command:**
   Place `skills/generate-changelog/SKILL.md` in your `.claude/skills/` directory to run `/generate-changelog` inside Claude Code.

---

## 🎯 Features

* **Tag-Aware:** Automatically detects the latest git tag and only documents unreleased commits.
* **Keep-a-Changelog Compliant:** Automatically organizes commits into `Added`, `Fixed`, `Changed`, `Removed`, `Security`, and `Maintenance`.
* **Zero Dependencies:** Pure POSIX Bash and Git — runs natively on macOS, Linux, and WSL without npm, pip, or external binaries.
* **Safe Prepending:** Prepends new releases to existing `CHANGELOG.md` while preserving header history.
