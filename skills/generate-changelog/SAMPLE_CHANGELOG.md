# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-10-21

### Added
- feat(dashboard): absorb Antigravity growth surface (/demo, /outreach, upgraded /pay, /contract) + SYNC.md [VERIFY: PASS] (`2da134c` by @Kunal)

### Fixed
- fix(ai): raise default max_tokens to 600 (gpt-oss reasoning + reply headroom) (`bc72dfc` by @Kunal)
- fix(ai): switch default model to openai/gpt-oss-120b (free-tier; llama moved to Enterprise) (`c70660e` by @Kunal)
- fix(supabase): valid idempotent policy syntax (drop+create) in schema.sql (`aba88d0` by @Kunal)

### Changed
- chore(gitignore): ignore .worktrees/ (`8cbc3e5` by @Kunal)
- chore(gitignore): exclude generated outreach CSVs (contact data) (`2dd92cf` by @Kunal)
- chore(repo): gitignore real config/*.json + README ship-to-GitHub checklist (`4b6a3de` by @Kunal)

