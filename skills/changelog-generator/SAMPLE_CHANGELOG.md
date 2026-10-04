# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased] - 2026-10-01

### Added
- FEAT-005: Self-healing pipeline recovery + automatic post-collection classification (`fea5f7d` by lam)
- RBASE-004: Add reproducible baseline verifier (`3300cbb` by lam)
- RBASE-002: Add repository hygiene manifest and checks (`c69053d` by lam)

### Fixed
- FIX-004: Wire classifier + revenue USD into scheduler cycle (`1a44549` by lam)
- FIX-003: Analytics classifier — ISO timestamp parse + early-stage WINNER threshold (`36fb0d5` by lam)
- FIX-002: Pre-flight probe for edge-tts to prevent bad file descriptor crash in daemon mode (`73052ec` by lam)
- FIX-001: Fail-closed payment reconciliation patch (`4eff98b` by lam)
- FIX-003: Restore explicit telemetry dashboard label (`ab7d778` by lam)
- FIX-002: Repair offline media and resource regression paths (`25752ea` by lam)
- RBASE-004: Fix verifier to inspect tracked files only (`f89f6a7` by lam)
- RFIX-001: Make payment reconciliation fail closed (`661c5e0` by lam)

### Changed
- BASELINE-004: Multi-platform publishing & upload queue reporting (`de2225f` by lam)
- BASELINE-003: Reproducible deployment package (`966c77e` by lam)
- BASELINE-003: Full dependency manifest + analytics promotion logic (`d452e16` by lam)
- BASELINE-002: Repository hygiene + real data pipeline upgrades (`56699b8` by lam)
- BASELINE-001: Import exact production code baseline (`5c7fc54` by lam)
- RBASE-003: Normalize package tree and retain only relative aliases (`0f29224` by lam)
- RBASE-001: Import production code truth without runtime state (`d159845` by lam)

