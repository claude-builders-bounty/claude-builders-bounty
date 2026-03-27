# Changelog Generator Skill

Automatically generate a structured `CHANGELOG.md` from git history.

## 🛠 Setup (3 Steps)
1. **Copy the script:** Download `changelog.sh` into your project root.
2. **Make executable:** Run `chmod +x changelog.sh`.
3. **Generate:** Run `./changelog.sh`.

## Claude Code Skill
This project also includes a `SKILL.md` file for direct integration with Claude Code agents.

### Usage
Once the skill is loaded, you can run it with:
`/generate-changelog`

To generate from a specific tag:
`/generate-changelog --since v1.0.0`

## ⚙️ How it works
The script fetches all commits since the last git tag (or the first commit if no tags exist) and categorizes them into:
- **Added:** Commits with "add" or "feat"
- **Fixed:** Commits with "fix" or "bug"
- **Changed:** Commits with "update", "change", or "refactor"
- **Removed:** Commits with "remove" or "delete"

---
**Sample Output:**
```markdown
# CHANGELOG
Generated on Thu Mar 26 19:50:00 PDT 2026

### Added
- add bounty hunter module (5806a21)
- add Coinbase monitor (b776680)

### Fixed
- fix path logic for secrets (5806a21)

### Changed
- update BOUNTIES.md with real targets (5806a21)
```
