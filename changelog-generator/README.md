# Git Changelog Generator 📝

Automated changelog generator that creates a Keep-a-Changelog compliant `CHANGELOG.md` directly from your Git history.

## 🚀 Setup & Usage in 3 Steps

1. **Download / Copy the script**
   ```bash
   chmod +x changelog.sh
   ```

2. **Run the script in any Git repository**
   ```bash
   bash changelog.sh
   ```

3. **Check your generated `CHANGELOG.md`**
   ```bash
   cat CHANGELOG.md
   ```

*(Optional: for Claude Code, copy `SKILL.md` to `.claude/skills/generate-changelog/SKILL.md` to invoke via `/generate-changelog`)*

---

## Features

- **Automatic Tag Detection**: Reads commits between the latest Git tag and `HEAD`. If no tag exists, it captures all commits.
- **Conventional Commits Parsing**: Automatically categorizes into:
  - `Added`: `feat:`, `add:`, `feature:`
  - `Fixed`: `fix:`, `bugfix:`, `hotfix:`
  - `Changed`: `refactor:`, `perf:`, `style:`, `ci:`, `build:`, `chore:`, `docs:`, `test:`, `update:`
  - `Removed`: `revert:`, `remove:`, `delete:`, `deprecate:`
- **Keep a Changelog standard**: Produces clean Markdown with commit hashes linked.
- **Customizable**:
  - `bash changelog.sh --output PATH`: Specify custom output filename
  - `bash changelog.sh --since TAG`: Specify starting tag
  - `bash changelog.sh --all`: Include all commits
  - `bash changelog.sh --version "v1.0.0"`: Override release header name
