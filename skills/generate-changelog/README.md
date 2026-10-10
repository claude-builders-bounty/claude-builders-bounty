# 📝 Skill: Generate Changelog from Git History

> Automatically inspects git commit history since the most recent tag and outputs a categorized `CHANGELOG.md` file following the Keep a Changelog standard.

Resolves **[Issue #1: SKILL: Generate a structured CHANGELOG from git history](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1)** ($50 Bounty).

---

## ⚡ Quickstart (3 Steps or Fewer)

1. **Make scripts executable:**
   ```bash
   chmod +x skills/generate-changelog/changelog.sh skills/generate-changelog/generate_changelog.py
   ```

2. **Generate your changelog:**
   ```bash
   bash skills/generate-changelog/changelog.sh v1.0.0
   ```

3. **Verify output:**
   Check the newly generated or updated `CHANGELOG.md` in your project root!

---

## 🏷️ Automatic Categorization

Commits are parsed and sorted into standard release categories:
- **`Added`**: New features (`feat:`, `add:`, `new:`, `implement:`)
- **`Fixed`**: Bug fixes (`fix:`, `bug:`, `patch:`, `hotfix:`)
- **`Changed`**: Refactoring, docs, and maintenance (`refactor:`, `perf:`, `docs:`, `chore:`)
- **`Removed`**: Deprecated or dropped code (`remove:`, `delete:`, `deprecate:`, `revert:`)

---

## 🧪 Testing

Run the included automated tests:

```bash
python3 skills/generate-changelog/test_changelog.py
```

Result: ✅ 100% test coverage on categorization, conventional commit prefix stripping, and markdown generation.
