# 📝 Automated Git Changelog Generator

Automatically parses git commits since the latest release tag and generates structured changelogs following [Keep a Changelog](https://keepachangelog.com/) standards.

## 🚀 3-Step Setup & Usage

### 1. Place in your repo
Copy `changelog.py` and `changelog.sh` into your project root.

### 2. Make executable (Optional for Linux/Mac)
```bash
chmod +x changelog.sh
```

### 3. Generate Changelog
```bash
python changelog.py v1.0.0
# Or
bash changelog.sh v1.0.0
```
This automatically inspects your git history and appends the new release notes to `CHANGELOG.md`.
