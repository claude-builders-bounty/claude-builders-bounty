# Git Changelog Generator 📋

> Automatically generate and update structured, categorized `CHANGELOG.md` files directly from your git history.

---

## ⚡ Quick Setup (3 Steps or Fewer)

1. **Copy the script or skill into your project:**
   ```bash
   mkdir -p scripts && cp skills/generate-changelog/scripts/changelog.py scripts/
   ```
2. **Make it executable:**
   ```bash
   chmod +x scripts/changelog.py
   ```
3. **Generate your changelog:**
   ```bash
   python3 scripts/changelog.py --output CHANGELOG.md
   ```

---

## 🛠 Usage & Options

```bash
# Preview unreleased changes to console
python3 scripts/changelog.py --dry-run

# Tag a new release (e.g. v1.0.0) and prepend to CHANGELOG.md
python3 scripts/changelog.py --version "v1.0.0" --output CHANGELOG.md

# Generate changes since a specific tag
python3 scripts/changelog.py --since "v0.9.0" --version "v1.0.0" --output CHANGELOG.md
```

## 🏷️ Conventional Commit Auto-Categorization

| Prefix | Changelog Section |
|---|---|
| `feat:` / `add:` | **Added** |
| `fix:` / `bugfix:` | **Fixed** |
| `refactor:` / `perf:` / `chore:` | **Changed** |
| `remove:` / `delete:` / `deprecate:` | **Removed** |
| `docs:` | **Documentation** |
| `security:` | **Security** |

Scoped commits (e.g., `feat(auth): add OAuth support`) automatically render as:
- **auth**: add OAuth support ([`abc1234`](https://github.com/owner/repo/commit/abc1234))
