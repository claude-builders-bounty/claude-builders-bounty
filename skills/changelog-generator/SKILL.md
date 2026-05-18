---
name: changelog-generator
description: Generate a structured CHANGELOG.md from git history
command: python3 skills/changelog-generator/changelog.py
---

# Changelog Generator

Fetches commits since the last git tag and categorizes them into **Added**, **Fixed**, **Changed**, **Removed**.

## Usage

```bash
/generate-changelog
# or
bash skills/changelog-generator/changelog.sh
python3 skills/changelog-generator/changelog.py
```
