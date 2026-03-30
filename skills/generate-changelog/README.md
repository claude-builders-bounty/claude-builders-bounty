# Generate Changelog (Claude Code Skill)

A native [Claude Code](https://docs.anthropic.com/claude-code/) skill that automatically reads your `git log` since the last tag, extracts raw project commit changes, intelligently categorizes them, and structures a perfect `CHANGELOG.md` entry.

## Requirements
- `git`
- Claude Code installed (`npm i -g @anthropic-ai/claude-code`)

## Setup Instructions
1. Copy this folder into your project's `.claude/skills` directory, or your user-level `~/.claude/skills` directory:
   ```bash
   mkdir -p ~/.claude/skills/generate-changelog
   cp SKILL.md ~/.claude/skills/generate-changelog/
   ```
2. In your terminal, launch Claude Code (`claude`).
3. Type `/generate-changelog` to run the skill.

## Example Input / Output
Claude will autonomously fetch:
```bash
git describe --tags --abbrev=0
git log v1.0.1..HEAD --pretty=format:"%s"
```

And formulate a structured markdown snippet before appending it:
```markdown
## [Unreleased] - 2026-03-30
### Added
- Core support for WebSockets.
- New authentication module with Base OAuth.
### Fixed
- Re-rendered navbar flickering issue on Safari.
### Changed
- Migrated primary database driver to libSQL.
```
