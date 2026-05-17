# 📋 CHANGELOG Generator

A bash script that automatically generates a structured `CHANGELOG.md` from your project's git history.

## Features

- ✅ Works with any git repository
- ✅ Auto-detects the last tag as the starting point
- ✅ Categorizes commits into: **Added**, **Fixed**, **Changed**, **Removed**
- ✅ Supports conventional commit prefixes (`feat:`, `fix:`, `refactor:`, etc.)
- ✅ Outputs properly formatted Markdown
- ✅ Option to generate full changelog (`--full` flag)
- ✅ Includes commit hashes for traceability
- ✅ Non-destructive — safe to run on any repo

## Usage (3 steps or fewer)

```bash
# 1. Make the script executable
chmod +x changelog.sh

# 2. Run it in your git repository
./changelog.sh

# 3. (Optional) Generate from all commits, ignoring tags
./changelog.sh CHANGELOG.md --full
```

That's it! Your `CHANGELOG.md` is ready to commit and share.

## Output format

```markdown
# Changelog

## [0.2.1] - 2026-05-17

### Added
- Add user authentication module (a1b2c3d)
- Implement rate limiting middleware (e4f5g6h)

### Fixed
- Fix login redirect loop (i7j8k9l)
- Correct timezone offset calculation (m0n1o2p)

### Changed
- Refactor database connection pool (q3r4s5t)
- Update dependency versions (u6v7w8x)

### Removed
- Drop legacy API v1 endpoints (y9z0a1b)
```

## Claude Code integration

Add as a custom slash command in your Claude Code config:

```json
{
  "commands": [
    {
      "name": "generate-changelog",
      "description": "Generate a CHANGELOG.md from git history",
      "command": "bash /path/to/changelog.sh"
    }
  ]
}
```

## Requirements

- `git` (any modern version)
- `bash` 4.0+
- A git repository with commit history

## Sample output

The `SAMPLE.md` file in this repo shows a real generated changelog from an active project.
