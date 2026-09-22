# Git Changelog Generator (Claude Code Skill)

Automatically generate a clean, structured `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) standards directly from your git commit history.

## 3-Step Setup & Usage

### 1. Place in Your Repository
Copy `changelog.sh` (and `SKILL.md` if using Claude Code) into the root of your project:
```bash
chmod +x changelog.sh
```

### 2. Run the Command
Generate your changelog from git history since the last release tag:
```bash
bash changelog.sh
```
*(Or inside Claude Code, run `/generate-changelog`)*

### 3. Review `CHANGELOG.md`
Open the generated `CHANGELOG.md` to see your commits neatly categorized into **Added**, **Fixed**, **Changed**, and **Removed**.

---

## Features
- **Auto-tag detection:** Automatically compares from the latest git tag (`git describe --tags --abbrev=0`) or all commits if no tags exist.
- **Conventional Commits & Semantic keywords:** Automatically parses `feat:`, `fix:`, `refactor:`, `chore:`, `remove:`, etc.
- **Dry-run mode:** Use `bash changelog.sh --dry-run` to preview the markdown without saving.
- **Custom output:** Specify a custom file with `bash changelog.sh -o RELEASE_NOTES.md`.
