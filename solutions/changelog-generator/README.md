# Git Changelog Generator

A zero-dependency bash tool and native Claude Code skill that automatically generates structured, [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) compliant release notes directly from git history.

## 🚀 Setup Instructions (3 Steps)

1. **Make Executable**:
   ```bash
   chmod +x skills/generate-changelog/changelog.sh
   ```

2. **Generate Changelog**:
   ```bash
   bash skills/generate-changelog/changelog.sh CHANGELOG.md
   ```

3. **Review Output**:
   Open `CHANGELOG.md` to view commits categorized into `Added`, `Fixed`, `Changed`, and `Removed`.

---

## 💡 Claude Code Skill Integration

You can invoke this skill directly inside Claude Code:
```text
/generate-changelog
```

## 📋 Categorization Rules

Supports both **Conventional Commits** and **Natural Imperative Language**:

| Category | Trigger Prefixes & Keywords | Example |
|---|---|---|
| **Added** | `feat:`, `feat(...):`, `add:`, `added:`, `new:`, `Add `, `Create `, `Implement ` | `feat(auth): add OAuth2 provider` |
| **Fixed** | `fix:`, `fix(...):`, `bugfix:`, `patch:`, `security:`, `Fix `, `Resolve ` | `fix(api): prevent null pointer exception` |
| **Changed** | `refactor:`, `perf:`, `chore:`, `style:`, `docs:`, `build:`, `ci:`, `test:`, `Update `, `Change ` | `refactor(db): optimize connection pool` |
| **Removed** | `remove:`, `removed:`, `revert:`, `deprecate:`, `Remove `, `Delete ` | `remove: drop deprecated v1 endpoints` |

## 🧪 Automated Test Suite

Run the isolated end-to-end test suite:
```bash
bash skills/generate-changelog/test_changelog.sh
```
Verifies 6 distinct scenarios (tag ranges, tagless repos, edge cases, special characters, empty repos) across 19 assertions.
