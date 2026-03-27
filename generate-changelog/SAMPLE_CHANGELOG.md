# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased] (since v1.2.0) — 2026-03-27

### Added

- Enhanced card panel — elapsed timer, stale detection, pipeline stages, retry/skip (`d4e9a51`)
- Map enriched executing task data to kanban working cards (`d6cfe77`)
- Extend KanbanCard for stale detection, add stale card styling (`c3ae7cd`)
- POST /api/tasks/retry endpoint for single-task retry and skip (`c855ed6`)
- WebSocket support for real-time dashboard updates (`a91f3e2`)

### Fixed

- Guard JSON.parse in CardPanel log rendering to prevent crash on malformed metadata (`bced759`)
- Race condition in concurrent task submissions (`7e2d4b1`)
- Correct timezone offset in scheduled task display (`3fc89a0`)

### Changed

- Upgrade dependencies to latest minor versions (`e5b1c23`)
- Refactor submission pipeline for better error propagation (`8d4f6a7`)
- Improve orchestrator logging with structured metadata (`f12e890`)

### Removed

- Deprecated v1 submission endpoint (`2ab7c91`)

---

*Generated with [generate-changelog](https://github.com/claude-builders-bounty/claude-builders-bounty)*
