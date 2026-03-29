# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2026-03-29

### Added
- feat: Allow passing null or undefined as the value for options in app.render (#6903)
- feat: do not modify the Content-Type twice when sending strings (#6991)

### Fixed
- fix: bump qs minimum to ^6.14.2 for CVE-2026-2391 (#7057)
- fix: search example to support Redis v4+ and Express 4/5 (#6274)
- fix: enhance req.acceptsCharsets method (#6088)

### Changed
- docs: replace dummy with placeholder in example comments (#7064)
- build(deps): bump actions/upload-artifact from 6.0.0 to 7.0.0 (#7074)
- build(deps): bump actions/download-artifact from 7.0.0 to 8.0.0 (#7073)
- build(deps): bump github/codeql-action from 4.32.0 to 4.32.4 (#7072)
- test: include edge case tests for `res.type()` (#7037)
- docs: fix README security policy link (#7029)
- Remove duplicate tests in res.location and res.jsonp (#6996)
- build(deps): bump github/codeql-action from 4.31.9 to 4.32.0 (#7013)
- build(deps): bump actions/setup-node from 6.1.0 to 6.2.0 (#7012)
- build(deps): bump actions/checkout from 6.0.1 to 6.0.2 (#7011)
- docs: Add @GroophyLifefor to the triage team (#6995)
- test: add test for normalizeType fallback when mime lookup fails (#6894)
- chore: remove benchmarks directory (#6992)
- test: added unit tests for utils.compileETag to cover valid and invalid inputs (#6534)
- docs: fix JSDoc for req.accepts() return value and parameter format (#6936)
- Polish HTML structure of the response in the res.redirect() function (#5167)
- docs: add @krzysdz to the triage team (#6482)
- build(deps): bump actions/setup-node from 6.0.0 to 6.1.0 (#6962)
- build(deps): bump actions/checkout from 6.0.0 to 6.0.1 (#6963)
- deps: qs@^6.14.1
- build(deps): bump github/codeql-action from 4.31.6 to 4.31.9 (#6964)
- build(deps): bump actions/upload-artifact from 5.0.0 to 6.0.0 (#6965)
- build(deps): bump actions/download-artifact from 6.0.0 to 7.0.0 (#6961)
- doc: fix security.md link to point to security tab
- docs: use global Security policy
