# Sample Output

Generated from [cli/cli](https://github.com/cli/cli) (GitHub's official CLI) using `bash changelog.sh -r /path/to/cli --dry-run`:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## v2.92.0 (2026-04-28)

### Added

- Add explicit build tags to platform-specific echo test files ([a44721d](https://github.com/cli/cli/commit/a44721d))
- Add missing //go:build integration tag to verify_integration_test.go ([20e4d25](https://github.com/cli/cli/commit/20e4d25))

### Fixed

- Update test assertion to match updated error message ([24c7b25](https://github.com/cli/cli/commit/24c7b25))
- Provide full path to copilot binary on exec error ([ae7bd54](https://github.com/cli/cli/commit/ae7bd54))
- Use CREATE_NO_WINDOW to prevent tzutil console flash on Windows ([3d9f22c](https://github.com/cli/cli/commit/3d9f22c))
- Fix triage-pull-requests skipping PRs that open as draft ([8fb4f33](https://github.com/cli/cli/commit/8fb4f33))
- Fix skills acceptance tests ([f47e459](https://github.com/cli/cli/commit/f47e459))
- Fix flaky Password test by increasing echo mode setup timeout ([6d6ea5f](https://github.com/cli/cli/commit/6d6ea5f))

### Changed

- Drop --repo gh-cli from dnf install lines ([084afb3](https://github.com/cli/cli/commit/084afb3))
- Bump google.golang.org/grpc from 1.81.0 to 1.81.1 ([93e0a28](https://github.com/cli/cli/commit/93e0a28))
- Derive digest algorithm from ref length in release verify commands ([5c437a8](https://github.com/cli/cli/commit/5c437a8))
- Bump golang.org/x/crypto from 0.50.0 to 0.51.0 ([712826a](https://github.com/cli/cli/commit/712826a))
- Simplify bump-go.sh toolchain logic ([e5f5427](https://github.com/cli/cli/commit/e5f5427))
- Rewrite script to use go mod edit instead of grep/sed ([355f507](https://github.com/cli/cli/commit/355f507))

### Removed

- Remove deprecated API endpoints ([c139b17](https://github.com/cli/cli/commit/c139b17))
```
