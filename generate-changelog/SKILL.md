# SKILL.md — Generate Changelog

## Usage

```
/generate-changelog [--since <tag>] [--output <file>]
```

Or via bash:

```bash
./changelog.sh [--since <tag>] [--output <file>]
```

## What It Does

1. Detects the last git tag automatically (or uses `--since <tag>`)
2. Fetches all commits since that tag
3. Categorizes commits using Conventional Commits + heuristic parsing:
   - **Added** — new features, new endpoints, new files
   - **Fixed** — bug fixes, patches, corrections
   - **Changed** — refactors, updates, improvements
   - **Removed** — deletions, deprecations, removals
4. Outputs a `CHANGELOG.md` in Keep-a-Changelog format

## Setup (3 Steps)

```bash
# 1. Save this skill as SKILL.md in your workspace
# 2. Make changelog.sh executable
chmod +x changelog.sh

# 3. Run
./changelog.sh
```

## Sample Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- New `/users` endpoint for user profile retrieval
- Python SDK wrapper for BoTTube API
- Unit tests for `calculate_reward` function

### Fixed
- Race condition in P2P message deduplication
- Wallet balance returning stale data on startup

### Changed
- Refactored `rustchain_p2p_gossip.py` to async/await
- Upgraded Python to 3.11+

### Removed
- Deprecated `/legacy/wallet/balance` endpoint
- Removed redundant `test_v1.py` file
```

## Implementation

See `changelog.sh` for the full implementation.

## Notes

- Requires: git, bash
- Works with any git repo
- Conventional Commits format (`feat:`, `fix:`, etc.) improves accuracy
- Falls back to heuristic parsing when conventional format not used
