# Git Changelog Generator

Automatically generate structured, production-ready `CHANGELOG.md` files from your project's git commit history.

## 3-Step Setup

1. **Copy into your repository:**
   Place `generate_changelog.py` and `changelog.sh` into your repo root (or `.scripts/` directory).

2. **Make executable:**
   ```bash
   chmod +x changelog.sh generate_changelog.py
   ```

3. **Generate your changelog:**
   ```bash
   ./changelog.sh 1.0.0
   ```
   *Your `CHANGELOG.md` will be created (or updated) following the [Keep a Changelog](https://keepachangelog.com) standard.*
