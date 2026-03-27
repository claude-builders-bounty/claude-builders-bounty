# /changelog — Generate CHANGELOG from Git History

A Claude Code skill that analyzes your git history and produces a structured, categorized CHANGELOG in Markdown format.

## Setup (3 steps)

1. Copy the `skills/changelog/` folder into your project's `.claude/skills/` directory:
   ```bash
   mkdir -p .claude/skills
   cp -r skills/changelog .claude/skills/
   ```

2. Register the skill in your `.claude/settings.json`:
   ```json
   {
     "skills": {
       "changelog": {
         "path": ".claude/skills/changelog/prompt.md",
         "invocation": "/changelog"
       }
     }
   }
   ```

3. Use it:
   ```
   /changelog
   /changelog v2.0.0..HEAD
   /changelog --format detailed
   /changelog last 20
   ```

## Output Formats

| Format | Description |
|--------|-------------|
| `keepachangelog` (default) | Follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) standard |
| `simple` | Minimal bullet-point list |
| `detailed` | Full table with authors, dates, and complete messages |

## Commit Categories

Commits are automatically categorized by their message prefix:

| Category | Triggers |
|----------|----------|
| Added | `feat:`, `add:`, "new", "implement", "create" |
| Changed | `update:`, `improve:`, `refactor:`, `enhance:` |
| Fixed | `fix:`, `bugfix:`, "resolve", "correct" |
| Removed | `remove:`, `delete:`, "drop", "deprecate" |
| Security | `security:`, "vuln", "cve", "auth" |

## Example Output

```markdown
# Changelog

## [Unreleased] - 2026-03-27

### Added
- User authentication with JWT tokens (a1b2c3d)
- Dark mode toggle in settings (e4f5g6h)

### Fixed
- Login form validation on mobile Safari (i7j8k9l)
- Memory leak in WebSocket handler (m0n1o2p)

### Changed
- Upgraded React from 18 to 19 (q3r4s5t)

### Security
- Patched XSS in comment rendering (u6v7w8x)
```

## License

MIT
