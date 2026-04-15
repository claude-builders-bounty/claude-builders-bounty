# Generate Changelog — Claude Code Skill

A Claude Code skill (SKILL.md) + bash script that automatically generates a structured CHANGELOG.md from a project's git history.

## Setup (3 Steps)

```bash
# 1. Save SKILL.md in your Claude Code workspace
# 2. Make the script executable
chmod +x changelog.sh

# 3. Run
./changelog.sh
```

Or use the Claude Code command:

```
/generate-changelog
```

## Features

- **Auto-detects last git tag** — no arguments required
- **Conventional Commits** — understands `feat:`, `fix:`, `refactor:`, etc.
- **Heuristic fallback** — intelligently categorizes non-standard commit messages
- **Keep-a-Changelog format** — ready to use or customize
- **No dependencies** — pure bash + git

## Sample Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- New `/users` endpoint for user profile retrieval
- Python SDK wrapper for BoTTube API

### Fixed
- Race condition in P2P message deduplication
- Wallet balance returning stale data on startup

### Changed
- Refactored `rustchain_p2p_gossip.py` to async/await

### Removed
- Deprecated `/legacy/wallet/balance` endpoint
```
