<!--
Sample output — generated verbatim by changelog.sh, no manual editing.

Repository: https://github.com/anthropics/anthropic-sdk-typescript
Reproduce with:

  git clone --filter=blob:none https://github.com/anthropics/anthropic-sdk-typescript.git
  cd anthropic-sdk-typescript
  for r in sdk-v0.112.0 sdk-v0.113.0 sdk-v0.114.0 sdk-v0.115.0; do
    bash ../changelog.sh --to "$r" --release "${r#sdk-}" --output CHANGELOG.md
  done
  bash ../changelog.sh --release "v0.116.0 (unreleased)" --output CHANGELOG.md

Each run appends one release section on top of the previous ones, which is how
the file below was built. A normal project just runs `bash changelog.sh` once
per release.
-->

# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.116.0 (unreleased)] - 2026-08-07

### Added

- Add `mid-conversation-tool-changes-2026-07-01` beta ([`c0a963e`](https://github.com/anthropics/anthropic-sdk-typescript/commit/c0a963e))
- Make bash timeout and abort errors matchable by class (#259) ([`6641c5e`](https://github.com/anthropics/anthropic-sdk-typescript/commit/6641c5e))
- Add support for session budgets, advisor tool, pinned inference location and skills auto-loading from GitHub ([`d72ff6a`](https://github.com/anthropics/anthropic-sdk-typescript/commit/d72ff6a))

### Changed

- Codegen metadata ([`3c4e1b3`](https://github.com/anthropics/anthropic-sdk-typescript/commit/3c4e1b3))
- Codegen related update ([`fbf135d`](https://github.com/anthropics/anthropic-sdk-typescript/commit/fbf135d))
- Small updates to descriptions ([`e421c43`](https://github.com/anthropics/anthropic-sdk-typescript/commit/e421c43))
- Bump @babel/core and @babel/helpers to 7.29.7 (#261) ([`501955c`](https://github.com/anthropics/anthropic-sdk-typescript/commit/501955c))
- Install tsc-multi from the npm registry (#265) ([`342d422`](https://github.com/anthropics/anthropic-sdk-typescript/commit/342d422))
- Updates to a few documentation strings ([`b7e95bf`](https://github.com/anthropics/anthropic-sdk-typescript/commit/b7e95bf))
- Refresh provider package dev tooling to mirror-available versions (#268) ([`dbfed51`](https://github.com/anthropics/anthropic-sdk-typescript/commit/dbfed51))
- Release main ([`ed02a89`](https://github.com/anthropics/anthropic-sdk-typescript/commit/ed02a89))

### Fixed

- Use hardcoded User-Agent strings instead of constructor names ([`0b3d4ae`](https://github.com/anthropics/anthropic-sdk-typescript/commit/0b3d4ae))

### Removed

- Remove retired Claude Opus 4.1 models ([`9efb7bd`](https://github.com/anthropics/anthropic-sdk-typescript/commit/9efb7bd))

## [v0.115.0] - 2026-07-24

### Added

- Add claude-opus-5 model ([`f298e9a`](https://github.com/anthropics/anthropic-sdk-typescript/commit/f298e9a))

### Changed

- Release main ([`3b45cd3`](https://github.com/anthropics/anthropic-sdk-typescript/commit/3b45cd3))

### Fixed

- Release abort listeners when requests settle (#1129) ([`ce8e54b`](https://github.com/anthropics/anthropic-sdk-typescript/commit/ce8e54b))

## [v0.114.0] - 2026-07-23

### Added

- Add new stop reason 'model_context_window_exceeded' ([`3d051df`](https://github.com/anthropics/anthropic-sdk-typescript/commit/3d051df))

### Changed

- Release main ([`2d314b4`](https://github.com/anthropics/anthropic-sdk-typescript/commit/2d314b4))

## [v0.113.0] - 2026-07-22

### Added

- Add support for Managed Agents model effort, initial session events, and threads delta streaming ([`1ec5566`](https://github.com/anthropics/anthropic-sdk-typescript/commit/1ec5566))

### Changed

- Release main ([`4414d47`](https://github.com/anthropics/anthropic-sdk-typescript/commit/4414d47))

## [v0.112.0] - 2026-07-16

### Added

- Add support for MCP Tunnels ([`d05ddf6`](https://github.com/anthropics/anthropic-sdk-typescript/commit/d05ddf6))

### Changed

- Codegen metadata ([`bc2d267`](https://github.com/anthropics/anthropic-sdk-typescript/commit/bc2d267))
- Release main ([`d4aa171`](https://github.com/anthropics/anthropic-sdk-typescript/commit/d4aa171))

