<!--
Generated from https://github.com/cli/cli
Range: v2.92.0..HEAD
Generated on: 2026-05-13
-->

# Changelog

## [Unreleased] - 2026-05-13

### Added
- Add missing //go:build integration tag to verify_integration_test.go
- Add explicit build tags to platform-specific echo test files

### Fixed
- Fix flaky Password test by increasing echo mode setup timeout
- Grammar fixes
- Fix skills acceptance tests
- Fix triage-pull-requests skipping PRs that open as draft
- fix(copilot): hint to run copilot directly when exec fails
- fix(copilot): provide full path to copilot binary on exec error
- fix(copilot): update test assertion to match updated error message

### Changed
- Update installation commands for GitHub CLI
- Print `gh auth refresh` for 401 returns
- Apply patch from code review feedback.
- chore(deps): bump goreleaser/goreleaser-action from 7.0.0 to 7.2.1
- Enable extended PR screening for external PRs
- Switch from actions/attest-build-provenance to actions/attest
- chore(deps): bump github.com/klauspost/compress from 1.18.5 to 1.18.6
- Bump copilot telemetry sampling to 100%
- Record accessibility state in telemetry
- Poll TTY echo mode instead of sleeping in password tests
- Address review feedback on echo mode polling
- Bump Go toolchain to 1.26.3
- chore(deps): bump golang.org/x/sys from 0.43.0 to 0.44.0
- chore(deps): bump golang.org/x/term from 0.42.0 to 0.43.0
- chore(deps): bump google.golang.org/grpc from 1.80.0 to 1.81.0
- chore(deps): bump golang.org/x/text from 0.36.0 to 0.37.0

### Removed
- Remove numberFieldOnly API shortcut
