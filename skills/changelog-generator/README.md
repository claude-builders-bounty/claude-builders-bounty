# 📋 CHANGELOG Generator

> Generate a structured `CHANGELOG.md` from git history with one command.

Automatically categorizes commits into **Added**, **Fixed**, **Changed**, **Removed**, **Security**, **Deprecated**, and **Other** sections — following the [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format.

---

## Setup (3 steps)

### 1. Download

```bash
curl -O https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/skills/changelog-generator/generate-changelog.sh
# Or (more features):
curl -O https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/skills/changelog-generator/generate_changelog.py
```

### 2. Make executable

```bash
chmod +x generate-changelog.sh
# Or:
chmod +x generate_changelog.py
```

### 3. Run

```bash
# In any git repository:
bash generate-changelog.sh

# Or with Python:
python generate_changelog.py
```

---

## Usage

### Basic

```bash
cd your-git-project
bash generate-changelog.sh
# → Creates CHANGELOG.md in current directory
```

### Advanced

```bash
# Specify repo and output path
bash generate-changelog.sh /path/to/repo docs/CHANGELOG.md

# Python version with options
python generate_changelog.py --repo /path/to/repo --output docs/CHANGELOG.md --tag-pattern release-*
```

### As a Claude Code Skill

Add this to your `CLAUDE.md`:

```markdown
## Skills
- ~/skills/generate-changelog/SKILL.md
```

Or define a slash command alias:

```markdown
## Commands
/generate-changelog: Run `bash ~/skills/generate-changelog/generate-changelog.sh` in the project root to generate CHANGELOG.md from git history.
```

Then simply ask: *"Generate a CHANGELOG for this project"* or use `/generate-changelog`

---

## Example Output

<details>
<summary>Click to expand</summary>

```markdown
# Changelog

## [v1.2.0] - 2025-01-15

### Added
- User authentication with OAuth2 ([abc1234](https://github.com/owner/repo/commit/abc1234))
- Rate limiting for API endpoints ([def5678](https://github.com/owner/repo/commit/def5678))

### Fixed
- Memory leak in session cache ([ghi9012](https://github.com/owner/repo/commit/ghi9012))
- Broken pagination on search results ([jkl3456](https://github.com/owner/repo/commit/jkl3456))

### Changed
- Upgraded dependencies to latest ([mno7890](https://github.com/owner/repo/commit/mno7890))
- Refactored database layer ([pqr1234](https://github.com/owner/repo/commit/pqr1234))
```
</details>

---

## Requirements

- **Git** (required for both versions)
- **Bash 3.2+** OR **Python 3.8+**
- No pip packages needed (stdlib only)

---

## License

MIT
