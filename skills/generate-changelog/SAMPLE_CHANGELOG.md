# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v1.2.0] - 2026-10-19 (since v1.1.0)

### Added
- Support for Claude 3.8 and Gemini 2.0 Flash models ([`a3f81c9`](a3f81c9)) by @alexdev
- Automatic retry mechanism on network timeouts ([`7c12eb4`](7c12eb4)) by @johndoe
- Multi-language export support (EN, ES, FR, DE) ([`b9921ef`](b9921ef)) by @sarah-codes

### Fixed
- Memory leak in background worker task pool ([`45f09ab`](45f09ab)) by @alexdev
- UTF-8 decoding error on non-ASCII commit characters on Windows ([`12ad90e`](12ad90e)) by @contributor

### Changed
- Refactored authentication middleware to support Bearer JWT tokens ([`68b13fc`](68b13fc)) by @lead-architect
- Upgraded dependencies to latest stable versions ([`09cd76b`](09cd76b)) by @bot-upgrade

### Removed
- Deprecated legacy v1 REST endpoints ([`e872c01`](e872c01)) by @lead-architect
