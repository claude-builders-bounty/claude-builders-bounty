# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v1.1.0] - 2026-09-19
> *Changes since `v1.0.0` (4 commits)*

### Added
- Pre-tool-use security hook blocking destructive bash commands (`[5dac29e]`)
- Automated changelog generator supporting Keep a Changelog standards (`[e8a109f]`)

### Changed
- Improved error messaging for blocked commands with exit code 2 (`[7c819a2]`)
- Updated README with 3-step quickstart guide (`[3b401f8]`)

### Fixed
- Trailing slash parsing in recursive directory removal checks (`[1d9c4e2]`)

## [v1.0.0] - 2026-09-01
> *Initial release or all commits (3 commits)*

### Added
- Initial project structure and test suite scaffolding (`[f81a7b0]`)
- Basic CLI entrypoint (`[a2b4c6e]`)
