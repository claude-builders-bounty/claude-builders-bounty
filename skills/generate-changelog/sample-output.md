# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and
[Conventional Commits](https://www.conventionalcommits.org/).

## [v2.93.0-preview] - 2026-05-10

### Added
- Add explicit build tags to platform-specific echo test files ([`a44721d`](https://github.com/cli/cli/commit/a44721d233be9a2f6f0b5ee5c4f71274acb8d296))
- Add missing //go:build integration tag to verify_integration_test.go ([`20e4d25`](https://github.com/cli/cli/commit/20e4d25147ea90d629d689a01675eac551fc6362))

### Changed
- **deps:** bump github.com/klauspost/compress from 1.18.5 to 1.18.6 ([`6dc432e`](https://github.com/cli/cli/commit/6dc432ec479a00b7fb272327d0e6fbb9350a5519))
- **deps:** bump goreleaser/goreleaser-action from 7.0.0 to 7.2.1 ([`ed31e2f`](https://github.com/cli/cli/commit/ed31e2f6e8b8079115409aec11c7960bf2360cc4))

### Fixed
- Fix triage-pull-requests skipping PRs that open as draft ([`8fb4f33`](https://github.com/cli/cli/commit/8fb4f3354cb61f30d204eb0673c20d0824e1cef8))
- Fix skills acceptance tests ([`f47e459`](https://github.com/cli/cli/commit/f47e459cf556aa492172491fbfb105af0b18e1b3))
- Fix flaky Password test by increasing echo mode setup timeout ([`6d6ea5f`](https://github.com/cli/cli/commit/6d6ea5f3719ca29802005d877b2beaa06beca7df))

### Removed
- Remove numberFieldOnly API shortcut ([`8ff70e6`](https://github.com/cli/cli/commit/8ff70e6e7ad6b2df3fd2a6988ed287189dd60ce2))

### Other
- Bump Go toolchain to 1.26.3 ([`cdda57e`](https://github.com/cli/cli/commit/cdda57e3601d2ce94ebae101d0dfa4983479ee6d))
- Address review feedback on echo mode polling ([`9c4184d`](https://github.com/cli/cli/commit/9c4184de6f8c208a11e4329b90fa9844efd728e9))
- Poll TTY echo mode instead of sleeping in password tests ([`c48bc1a`](https://github.com/cli/cli/commit/c48bc1a7d1f4adc9dca524ef99435291b35c24b5))
- Record accessibility state in telemetry ([`acf2f73`](https://github.com/cli/cli/commit/acf2f730c19dd0bc904969e58a133776698caaf0))
- Bump copilot telemetry sampling to 100% ([`1caa3b7`](https://github.com/cli/cli/commit/1caa3b7475611186a617071106dd415e996b25f1))
- Grammar fixes ([`d8b8655`](https://github.com/cli/cli/commit/d8b8655f2199bbda719d56a38943d69031095e3a))
- Switch from actions/attest-build-provenance to actions/attest ([`4ed7002`](https://github.com/cli/cli/commit/4ed70026815d71b97b54d2ceeb038e992a34fd55))
- Enable extended PR screening for external PRs ([`8b89c8b`](https://github.com/cli/cli/commit/8b89c8b2b2eb9920f944bf3091fda5724ddee717))
- Apply patch from code review feedback. ([`c139b17`](https://github.com/cli/cli/commit/c139b17e9fe007126d9e44d1bd8bab7bac2943f5))
- Print `gh auth refresh` for 401 returns ([`a656271`](https://github.com/cli/cli/commit/a656271f26a591c958f561874ddced4aace18bed))
