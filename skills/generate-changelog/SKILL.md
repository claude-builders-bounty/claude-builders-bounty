---
name: generate-changelog
description: Automatically generate a structured Keep-a-Changelog compliant CHANGELOG.md from git commit history since the latest git tag.
---

# Generate Structured CHANGELOG Skill

Use this skill whenever the user asks to generate, update, or preview a `CHANGELOG.md` from git history, or invokes `/generate-changelog`.

## Workflow

1. **Detect Tag Range:**
   - Check the most recent git tag via `git describe --tags --abbrev=0`.
   - If a tag exists, collect commits in `LATEST_TAG..HEAD`. If no tags exist yet, collect all commits up to `HEAD`.
2. **Categorize Commits:**
   - Group commits into standard [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) sections:
     - **Added**: `feat`, `add`, `new`
     - **Fixed**: `fix`, `bug`, `hotfix`, `patch`
     - **Changed**: `refactor`, `perf`, `change`, `update`, `chore`, `style`, `docs`, `build`, `ci`
     - **Removed**: `remove`, `delete`, `drop`, `deprecate`
     - **Security**: `security`, `sec`, `vuln`, `cve`
3. **Execute Generator:**
   - On Linux/macOS/Git Bash:
     ```bash
     bash ./changelog.sh --output CHANGELOG.md
     ```
   - On Windows / Cross-Platform Node.js:
     ```bash
     node ./changelog.mjs --output CHANGELOG.md
     ```
4. **Verify Output:**
   - Ensure every entry includes the short commit hash (`7 chars`), clean commit subject (with conventional prefix stripped), and author attribution.
