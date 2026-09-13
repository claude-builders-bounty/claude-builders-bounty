# Changelog

> Sample generated against the real public repo [cli/cli](https://github.com/cli/cli) with:
> `bash changelog.sh --since v2.99.0 --stdout` on 2026-09-13
> (bullet lists truncated to ~6 per section for PR readability).

All notable changes are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased (since v2.99.0)] - 2026-09-13

Compare: https://github.com/cli/cli/compare/v2.99.0...HEAD

### Added

- Add clipboard preference for auth flows (`cbe0458`)
- Add trustworthy VHS demo skill (`d4d6e70`)
- Add webhook as an official extension (`d00109a`)
- Add a raw response request surface to api.Client (`62a6e9e`)
- Add the api_host gateway harness (`eae00d0`)
- Add acceptance coverage for gist (`c219743`)
- … (more in full run)

### Fixed

- Fix remote branch deletion for owner case mismatch (#14429) (`8fcd6a6`)
- Fix acceptance script paths on Windows (`3b3093f`)
- Fix Go bump workflow toolchain (`69e69c1`)
- Fix VHS evidence inspection (`b174ed5`)
- Fix gh api telemetry disablement (`4a75987`)
- Fix scriptfilter table field alignment (`95107ff`)
- … (more in full run)

### Changed

- Retire multi-account migration (#14430) (`ba51bb4`)
- Update Go bump validation tools (`d171a91`)
- Bump golang.org/x/sys from 0.47.0 to 0.48.0 (`9a779be`)
- Propagate gh path to extensions (`3041965`)
- Validate repository names during interactive creation (#14313) (`9174ffb`)
- Rewrite CLI agent guidance (`f537efa`)
- … (more in full run)

### Removed

- Delete repo garden command (`5448cdc`)
- Remove GH_EXTENSION help text per review feedback (`c708a53`)
- Remove redundant searcher comment (`05a0a02`)
- Remove unnecessary 204 on release edit (`0580da9`)
- Remove redundant comment in gist create (`6e7b1fe`)
