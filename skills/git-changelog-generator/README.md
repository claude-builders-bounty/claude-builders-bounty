# Git Changelog Generator Skill for Claude Code 📝

An autonomous skill and standalone CLI tool to automatically extract, categorize, and format git commits into a clean `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and [Semantic Versioning](https://semver.org/).

---

## ⚡ Quick Setup (3 Steps)

### Step 1: Copy Skill to Your Project
```bash
cp -r skills/git-changelog-generator your-project/skills/
```

### Step 2: Run via Claude Code or CLI
Inside Claude Code prompt:
```
/generate-changelog
```
Or directly from your terminal:
```bash
python3 skills/git-changelog-generator/generate_changelog.py --version "v1.2.0"
```

### Step 3: Review Your `CHANGELOG.md`
Your formatted `CHANGELOG.md` is instantly generated and categorized into:
- 🚀 **Added**: New features (`feat:`, `add:`)
- 🐛 **Fixed**: Bug resolutions (`fix:`, `patch:`)
- 🔄 **Changed**: Refactors, updates, performance (`refactor:`, `perf:`)
- 🗑️ **Removed**: Deprecated/removed code
- 🛡️ **Security**: Security hardening (`security:`, `cve:`)
- 📚 **Documentation**: Docs updates (`docs:`)

---

## 🧪 Automated Testing

Run the test suite to verify categorizer logic:
```bash
python3 -m unittest skills/git-changelog-generator/tests/test_changelog.py
```
