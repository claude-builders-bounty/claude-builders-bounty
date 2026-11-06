# Claude Code Skill: Structured CHANGELOG Generator (`#1`)

Automatically parses git commit history since the latest tag (`git describe --tags --abbrev=0`) and generates a clean, [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)-compliant `CHANGELOG.md` grouped into **Added**, **Fixed**, **Changed**, **Removed**, and **Security**.

---

## Quick 3-Step Setup

1. **Copy the Skill & Script into your repository:**
   Place `SKILL.md`, `.claude/commands/generate-changelog.md`, and `changelog.sh` (plus `changelog.mjs` for cross-platform Windows/macOS/Linux support) into your project root.
2. **Make the script executable (Linux/macOS/Git Bash):**
   ```bash
   chmod +x changelog.sh
   ```
3. **Run via Claude Code or CLI:**
   - **Inside Claude Code:** Type `/generate-changelog`
   - **Via Bash:** `./changelog.sh --output CHANGELOG.md --version v1.1.0`
   - **Via Node.js (Cross-Platform):** `node changelog.mjs --output CHANGELOG.md --version v1.1.0`
