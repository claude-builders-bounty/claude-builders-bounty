# Git Changelog Generator (`SKILL.md` & `changelog.sh`)

> 💰 Built for [Claude Builders Bounty #1](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1) — Powered by Opire

Automatically generates a structured, human-readable `CHANGELOG.md` from git commit history, categorized into **Added**, **Fixed**, **Changed**, and **Removed**.

---

## ⚡ 3-Step Quick Start

### Step 1: Clone / Copy to your project
```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
cd claude-builders-bounty
```

### Step 2: Make executable
```bash
chmod +x changelog.sh generate_changelog.py
```

### Step 3: Run generator
```bash
./changelog.sh
```
*That's it! Your `CHANGELOG.md` is generated in the root directory.*

---

## 🛠 Features

- **Auto Tag Detection:** Automatically fetches commits since the latest git tag (`git describe --tags`).
- **Smart Classification:** Categorizes commits using Conventional Commits (`feat:`, `fix:`, `refactor:`, etc.) and natural keywords.
- **Keep a Changelog Standard:** Produces valid Markdown adhering to [keepachangelog.com](https://keepachangelog.com/).
- **Claude Code Skill Compatible:** Includes `SKILL.md` for native `/generate-changelog` execution in Claude Code.

---

## 📖 CLI Flags

```bash
# Print to console instead of writing file
./changelog.sh --stdout

# Output to custom path
./changelog.sh -o docs/HISTORY.md

# Generate commits since a specific tag or commit hash
./changelog.sh --since v1.2.0

# Custom release section title
./changelog.sh --tag "v2.0.0-rc1"
```

---

## 🧪 Testing

Run unit tests with `pytest`:
```bash
python3 -m unittest tests/test_changelog.py
```
