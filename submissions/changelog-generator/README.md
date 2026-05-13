# Changelog Generator Skill for Claude Code

A comprehensive Claude Code skill that generates structured `CHANGELOG.md` from git history with automatic categorization.

## Features

- 🏷️ **Auto-categorization**: Intelligently sorts commits into Added/Fixed/Changed/Removed/Security/Breaking
- 📝 **Conventional Commits**: Full support for `feat:`, `fix:`, `refactor:`, etc.
- 🔍 **Smart heuristics**: Falls back to keyword analysis for non-conventional commits
- 📋 **Multiple formats**: Markdown (default), JSON, and HTML output
- 🎯 **Scoped grouping**: Groups changes by scope (`feat(api):`, `fix(ui):`)
- 👥 **Contributor credit**: Optional contributor attribution
- ⚙️ **Configurable**: `.changelogrc` for custom categories and behavior
- 🔄 **Incremental**: Preserves existing changelog entries
- 📦 **Monorepo support**: Detects and handles subdirectory packages

## Setup (3 steps or fewer)

1. Copy `SKILL.md` to your project's `.claude/skills/generate-changelog/` directory:
   ```bash
   mkdir -p .claude/skills/generate-changelog
   cp SKILL.md .claude/skills/generate-changelog/
   ```

2. That's it. No dependencies required.

3. Use it: Type `/generate-changelog` in Claude Code.

## Usage

```
/generate-changelog              # Generate since last tag
/generate-changelog --from v1.0  # Generate from specific tag
/generate-changelog --full       # Include all sections (even empty)
/generate-changelog --credit     # Include contributor names
/generate-changelog --dry-run    # Preview without writing
/generate-changelog --format json  # Output as JSON
```

## Sample Output

```markdown
# Changelog

## [1.3.0] - 2026-05-13

### Added
- Add streaming response support for WebSocket endpoints (a3f2b1c)
- Implement rate limiting middleware (d4e5f6a)

### Fixed
- Handle concurrent session cleanup without deadlock (e1f2a3b)
- Resolve memory leak in worker processes (c4d5e6f)

### Changed
- Improve query planner performance for complex joins (j1k2l3m)

### Security
- Patch CVE-2026-1234 in dependency chain (r8s9t0u)
```

## How It Works

1. Detects the last git tag
2. Collects all non-merge commits since that tag
3. Categorizes each commit using conventional commit prefixes + keyword heuristics
4. Formats entries according to [Keep a Changelog](https://keepachangelog.com/) standard
5. Previews the result and asks for confirmation before writing

## Tested On

- Node.js projects (package.json)
- Python projects (pyproject.toml)
- Rust projects (Cargo.toml)
- Go projects (go.mod)
- Plain git repos

## License

MIT
