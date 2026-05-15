# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Commits are parsed using the [Conventional Commits](https://www.conventionalcommits.org/) specification.

## [v0.5.0] - 2026-05-15

### Added

  - Add JWT token refresh endpoint ([a1b2c3d](https://github.com/username/project/commit/a1b2c3d))
  - Add rate limiting to API routes ([b2c3d4e](https://github.com/username/project/commit/b2c3d4e))
  - Add database migration for user preferences ([c3d4e5f](https://github.com/username/project/commit/c3d4e5f))

### Fixed

  - Correct date formatting in email templates ([d4e5f6g](https://github.com/username/project/commit/d4e5f6g))
  - Resolve crash on empty search query ([e5f6g7h](https://github.com/username/project/commit/e5f6g7h))
  - Fix XSS vulnerability in profile form ([f6g7h8i](https://github.com/username/project/commit/f6g7h8i))

### Changed

  - Extract validation logic into shared module ([g7h8i9j](https://github.com/username/project/commit/g7h8i9j))
  - Reformat all files with Prettier v3 ([h8i9j0k](https://github.com/username/project/commit/h8i9j0k))

### Deprecated

  - Mark legacy v1 API endpoints as deprecated ([i9j0k1l](https://github.com/username/project/commit/i9j0k1l))

### Removed

  - Delete deprecated v1 API endpoints ([j0k1l2m](https://github.com/username/project/commit/j0k1l2m))

### Security

  - Fix SQL injection vulnerability in login ([k1l2m3n](https://github.com/username/project/commit/k1l2m3n))
  - Update encryption algorithm to AES-256 ([l2m3n4o](https://github.com/username/project/commit/l2m3n4o))

### Performance

  - Optimize database queries for feed endpoint ([m3n4o5p](https://github.com/username/project/commit/m3n4o5p))
  - Improve image loading with lazy loading ([n4o5p6q](https://github.com/username/project/commit/n4o5p6q))

---

_11 categorized commits out of 14 total (2 breaking)_

## [v0.4.0] - 2026-04-01

### Added

  - Add user notification preferences
  - Add dark mode toggle

### Fixed

  - Fix logout not clearing session
  - Fix mobile navigation overlap

### Changed

  - Upgrade to React 19
  - Refactor authentication middleware

### Performance

  - Reduce bundle size with code splitting

---

_6 categorized commits out of 8 total_

## [v0.3.0] - 2026-03-01

### Added

  - Add search functionality with Elasticsearch
  - Add pagination to API responses

### Fixed

  - Fix timeout on large dataset exports
  - Fix WebSocket reconnection logic

### Changed

  - Update dependency: lodash → lodash-es

### Removed

  - Remove jQuery dependency

---

_6 categorized commits out of 6 total_

---

## Raw Input Example

The following conventional commits were used to generate the changelog above:

```text
feat: add JWT token refresh endpoint
feat: add rate limiting to API routes
feat: add database migration for user preferences
fix: correct date formatting in email templates
fix: resolve crash on empty search query
fix: fix XSS vulnerability in profile form
refactor: extract validation logic into shared module
style: reformat all files with Prettier v3
deprecate: mark legacy v1 API endpoints as deprecated
remove: delete deprecated v1 API endpoints
security: fix SQL injection vulnerability in login
security: update encryption algorithm to AES-256
perf: optimize database queries for feed endpoint
perf: improve image loading with lazy loading
```

### Command Used

```bash
bash skills/generate-changelog/changelog.sh --since v0.3.0
```
