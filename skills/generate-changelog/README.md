# Changelog Generator Skill

Generates a structured `CHANGELOG.md` from git history, auto-categorizing
commits into Added, Fixed, Changed, and Removed sections.

## Setup (3 steps)

1. Copy `changelog.sh` or `changelog.py` to your project root
2. Make executable: `chmod +x changelog.py`
3. Run: `python3 changelog.py`

## Features

- Fetches commits since the last git tag
- Auto-categorizes by conventional commit prefixes (`feat:`, `fix:`, `refactor:`, etc.)
- Outputs properly formatted `CHANGELOG.md`
- Appends to existing changelog if one exists

## Example Output

```markdown
# Changelog

## [v1.2.0] - 2026-05-16

### Added
- Add user authentication endpoint
- Add dark mode toggle

### Fixed
- Fix race condition in WebSocket handler
- Fix memory leak in cache layer
```

## Usage with Claude Code

You can add this as a SKILL.md in your `.claude/` directory:

```markdown
# SKILL: Generate Changelog

Run `python3 changelog.py` to generate a structured CHANGELOG.md from git history.
The script auto-categorizes commits and appends to existing changelog.
```

Tested on real GitHub repositories with conventional commit format.
