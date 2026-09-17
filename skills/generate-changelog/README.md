# 📜 Generate Changelog Skill (`/generate-changelog`)

An automated tool & Claude Code skill that parses git history and generates a structured, human-readable `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com) conventions.

---

## 🚀 Quick Setup (3 Steps or Fewer)

1. **Clone or Copy**: Place the `skills/generate-changelog` folder in your repository or `~/.claude/skills/`.
2. **Make Executable**:
   ```bash
   chmod +x skills/generate-changelog/changelog.sh
   ```
3. **Run**:
   ```bash
   # Generate unreleased changes
   ./skills/generate-changelog/changelog.sh

   # Or specify a release version
   ./skills/generate-changelog/changelog.sh v1.0.0
   ```

---

## ⚡ Features

- 🏷️ **Tag-Aware**: Automatically identifies the latest git tag using `git describe --tags --abbrev=0` and aggregates commits since that tag.
- 📂 **Semantic Categorization**: Automatically categorizes commits into:
  - **Added**: New features, endpoints, capabilities (`feat:`, `add:`, `implement:`)
  - **Fixed**: Bug resolutions, patches, issue closures (`fix:`, `patch:`, `resolve:`, `close #...`)
  - **Changed**: Refactoring, optimizations, dependency updates, documentation (`refactor:`, `perf:`, `docs:`, `chore:`)
  - **Removed**: Cleanups, deprecations, dropped features (`remove:`, `deprecate:`)
- 📄 **Keep a Changelog Formatting**: Outputs standardized Markdown with release version, date, categorized bullet points, and commit hashes.
- 🤖 **Claude Code Integration**: Includes `SKILL.md` for seamless invocation via `/generate-changelog`.

---

## 🧪 Testing

```bash
python3 skills/generate-changelog/test_changelog.py
```
Output:
```
Ran 5 tests in 0.001s
OK
```
