# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v1.2.0] - 2026-10-17
*Changes since tag `v1.1.0`:*

### Added
- **auth**: add Passkey and WebAuthn multi-factor support ([`4f2e1a9`](https://github.com/example/repo/commit/4f2e1a9))
- **billing**: support automated tax calculation via Stripe Tax ([`9b3d7c2`](https://github.com/example/repo/commit/9b3d7c2))
- **api**: export OpenAPI v3.1 specification endpoint ([`e6a18d4`](https://github.com/example/repo/commit/e6a18d4))

### Fixed
- **session**: resolve race condition during concurrent token refresh ([`1d8c4e0`](https://github.com/example/repo/commit/1d8c4e0))
- **sqlite**: prevent database lock timeouts by setting WAL busy timeout to 5000ms ([`8f2c3b1`](https://github.com/example/repo/commit/8f2c3b1))

### Changed
- **core**: upgrade Next.js to 15.2 and React to 19.1 ([`5c4a9f8`](https://github.com/example/repo/commit/5c4a9f8))
- **db**: optimize subscriber indexing for high-cardinality multi-tenant lookups ([`3a2b1c0`](https://github.com/example/repo/commit/3a2b1c0))

### Removed
- **legacy**: drop deprecated v1 REST webhook dispatcher ([`7e6d5c4`](https://github.com/example/repo/commit/7e6d5c4))

### Security
- **deps**: upgrade jsonwebtoken to address CVE-2026-38291 ([`6f5e4d3`](https://github.com/example/repo/commit/6f5e4d3))

---

## [v1.1.0] - 2026-09-15

### Added
- **ui**: initial dark mode theme toggle ([`2a1b0c9`](https://github.com/example/repo/commit/2a1b0c9))
- **sqlite**: embedded better-sqlite3 database layer ([`1a2b3c4`](https://github.com/example/repo/commit/1a2b3c4))
