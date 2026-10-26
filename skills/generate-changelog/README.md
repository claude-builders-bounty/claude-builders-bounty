# 📝 Git Changelog Generator for Claude Code

Automatically generates a structured, human-readable `CHANGELOG.md` directly from your Git commit history. Follows the [Keep a Changelog](https://keepachangelog.com/) standard and auto-categorizes commits using Conventional Commits.

---

## ⚡ Setup & Usage in 3 Steps

### Step 1: Clone or Copy
Place `skills/generate-changelog` into your repository or `~/.claude/skills/generate-changelog`.

### Step 2: Run the Generator
Run with either Python or Bash:
```bash
# Cross-platform (Python 3.8+)
python skills/generate-changelog/changelog.py --version v1.0.0

# Or using Bash
bash skills/generate-changelog/changelog.sh CHANGELOG.md v1.0.0
```

### Step 3: Inspect Output
Open your updated `CHANGELOG.md` with organized `Added`, `Fixed`, `Changed`, `Removed`, and `Maintenance` sections!

---

## 🏷️ Category Mapping

| Commit Prefix / Keyword | Changelog Category | Example |
| :--- | :--- | :--- |
| `feat:`, `feature:`, `add:` | **Added** | `- Add biometric authentication` |
| `fix:`, `bugfix:`, `patch:` | **Fixed** | `- Fix race condition in cache eviction` |
| `refactor:`, `perf:`, `change:` | **Changed** | `- Optimize SQL query planner` |
| `remove:`, `deprecate:`, `drop:` | **Removed** | `- Remove legacy v1 endpoints` |
| `chore:`, `docs:`, `test:`, `ci:` | **Maintenance** | `- Update CI test matrices` |

---

## 🧪 Testing

Run automated tests:
```bash
python skills/generate-changelog/test_changelog.py
```
