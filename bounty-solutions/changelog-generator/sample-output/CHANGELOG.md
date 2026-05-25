# Changelog

Generated from `git log v2.92.0..HEAD`

## Added

- Add 3 day dependabot cooldown period (d4a57fe)
- Add explicit build tags to platform-specific echo test files (a44721d)
- Add missing //go:build integration tag to verify_integration_test.go (20e4d25)

## Fixed

- fix(copilot): update test assertion to match updated error message (24c7b25)
- fix(copilot): provide full path to copilot binary on exec error (ae7bd54)
- fix(copilot): hint to run copilot directly when exec fails (601dd34)
- fix(telemetry): use CREATE_NO_WINDOW to prevent tzutil console flash on Windows (3d9f22c)
- Fix triage-pull-requests skipping PRs that open as draft (8fb4f33)
- Fix skills acceptance tests (f47e459)
- Fix flaky Password test by increasing echo mode setup timeout (6d6ea5f)

## Changed

- bump golang.org/x/net (be4ad7e)
- Link to Accessibility category for community discussions instead of ACR (#13481) (87c8d19)
- Allow agents as application for secrets (#13421) (e60f00e)
- SHA pin first-party GitHub Actions (94e3b1f)
- chore(deps): bump github/codeql-action from 4 to 4.35.5 (01e0b8d)
- chore(deps): bump github.com/google/go-containerregistry (386d72e)
- Run govulncheck daily instead of weekly (a9026fd)
- Merge pull request #13486 from cli/tommy/update-x-crypto (1bfcf1c)
- Potential fix for pull request finding (230498e)
- Potential fix for pull request finding (69148fb)
- Stop bumping homebrew on release (b49fc31)
- chore(deps): bump goreleaser/goreleaser-action from 7.2.1 to 7.2.2 (#13461) (6bbaae0)
- chore(deps): bump github.com/theupdateframework/go-tuf/v2 (abac9a1)
- docs: drop --repo gh-cli from dnf install lines (084afb3)
- Assert digest prefix in release verify no-attestation tests (d9eb062)
- chore(deps): bump google.golang.org/grpc from 1.81.0 to 1.81.1 (93e0a28)
- Derive digest algorithm from ref length in release verify commands (5c437a8)
- docs: fix duplicated "of" in release-process-deep-dive (8bef879)
- chore(deps): bump golang.org/x/crypto from 0.50.0 to 0.51.0 (712826a)
- Simplify bump-go.sh toolchain logic (e5f5427)
- Rewrite script to use go mod edit instead of grep/sed (355f507)
- Address code review comments (209ef1d)
- Improve version comparison to handle both X.Y.0 and X.Y.Z formats (653ffc2)
- Update bump-go.sh to handle missing toolchain directive (f561003)
- Initial plan (8c69492)
- Update CODEOWNERS for skills directory ownership (83bc3de)
- chore(deps): bump golang.org/x/text from 0.36.0 to 0.37.0 (dc5d392)
- chore(deps): bump google.golang.org/grpc from 1.80.0 to 1.81.0 (6b3421b)
- chore(deps): bump golang.org/x/term from 0.42.0 to 0.43.0 (965f63b)
- chore(deps): bump golang.org/x/sys from 0.43.0 to 0.44.0 (701492b)
- Bump Go toolchain to 1.26.3 (cdda57e)
- Address review feedback on echo mode polling (9c4184d)
- Poll TTY echo mode instead of sleeping in password tests (c48bc1a)
- Record accessibility state in telemetry (acf2f73)
- Bump copilot telemetry sampling to 100% (1caa3b7)
- chore(deps): bump github.com/klauspost/compress from 1.18.5 to 1.18.6 (6dc432e)
- Grammar fixes (d8b8655)
- Switch from actions/attest-build-provenance to actions/attest (4ed7002)
- Enable extended PR screening for external PRs (8b89c8b)
- chore(deps): bump goreleaser/goreleaser-action from 7.0.0 to 7.2.1 (ed31e2f)
- Apply patch from code review feedback. (c139b17)
- Print `gh auth refresh` for 401 returns (a656271)
- Update installation commands for GitHub CLI (ba33308)

## Removed

- Remove discussion workflow (6b5e3bc)
- Remove dependency on persistent token (57480dd)
- Remove third-party license debris (3faf4e9)
- Remove unnecessary null checks in jq output handling (d2cc91b)
- Remove numberFieldOnly API shortcut (8ff70e6)

