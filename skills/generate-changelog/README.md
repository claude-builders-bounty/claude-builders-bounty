# Structured CHANGELOG Generator Skill — Issue #1

Generates a clean `CHANGELOG.md` from git history since the last git tag, auto-categorizing commits into **Added**, **Fixed**, **Changed**, and **Removed**.

## Setup & Usage (2 Steps)

```bash
chmod +x skills/generate-changelog/generate_changelog.py
python3 skills/generate-changelog/generate_changelog.py --repo . --output CHANGELOG.md
```

## Sample Output (Tested on Real Git Repository)

```markdown
# Changelog

## [Unreleased] (since v1.2.0)

### Added
- feat(hook): Add pre-tool-use destructive bash command blocker (#3) (c8b529c)

### Fixed
- fix(parser): Handle combined short flags in command evaluator (a19bc04)

### Changed
- refactor(cli): Streamline structured markdown output formatting (7f31e21)

### Removed
- chore: Remove deprecated legacy config stub (0d92a11)
```
