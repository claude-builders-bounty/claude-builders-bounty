# Git History CHANGELOG Generator 📜

Automatically generate and maintain a structured `CHANGELOG.md` following the [Keep a Changelog](https://keepachangelog.com) standard directly from your git history.

---

## 🚀 Setup in 3 Steps

### 1. Make executable
```bash
chmod +x changelog.sh
```

### 2. Generate Changelog
```bash
./changelog.sh
```

### 3. Review Generated File
Inspect your newly generated or updated `CHANGELOG.md` in the project root:
```bash
cat CHANGELOG.md
```

---

## 🏷️ Commit Categorization Rules

The generator parses conventional commit conventions into standard sections:

| Category | Commit Prefixes |
|---|---|
| **Added** | `feat:`, `add:`, `feature:` |
| **Fixed** | `fix:`, `bug:`, `patch:`, `resolve:` |
| **Changed** | `refactor:`, `perf:`, `update:`, `change:` |
| **Removed** | `remove:`, `delete:`, `deprecate:` |
| **Security** | `sec:`, `security:` |
| **Documentation** | `docs:`, `doc:` |
| **Other** | All other commit messages |

---

## 🧪 Verification & Unit Tests

Zero external dependencies:
```bash
python3 -m unittest tests/test_generate_changelog.py -v
```
