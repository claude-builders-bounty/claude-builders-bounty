# Changelog

## [Unreleased]

### Fixed
- fix(acp): replay assistant reasoning as agent_thought_chunk on session/load (#12285) (#26943) ([`f3a4af9`](https://github.com/.../commit/f3a4af9))
- fix(security): separate OAuth PKCE state from code_verifier ([`fcd9011`](https://github.com/.../commit/fcd9011))
- fix(gateway): merge rapid TEXT follow-ups during active sessions (#4469) (#26822) ([`585d6b6`](https://github.com/.../commit/585d6b6))
- fix(copilot-acp): tighten deprecation detection + sharpen GitHub Models 413 hint ([`374dc81`](https://github.com/.../commit/374dc81))
- fix: detect gh-copilot deprecation and improve GitHub Models 413 errors (#10648) ([`4ded3ed`](https://github.com/.../commit/4ded3ed))
- fix(doctor): suppress stale direct-key issues when oauth is healthy ([`d0a183c`](https://github.com/.../commit/d0a183c))

### Changed
- style: move secrets import alongside other function-level imports ([`345821b`](https://github.com/.../commit/345821b))

### Testing
- test(security): regression guard for OAuth PKCE state/verifier separation ([`72f94f4`](https://github.com/.../commit/72f94f4))
- test: add tests for copilot ACP deprecation detection and Azure URL mapping ([`b85b938`](https://github.com/.../commit/b85b938))

### Maintenance
- chore: release v0.14.0 (2026.5.16) (#26862) ([`a91a57f`](https://github.com/.../commit/a91a57f))
- chore: add worlldz to AUTHOR_MAP for #26704 salvage ([`7bb97b9`](https://github.com/.../commit/7bb97b9))

## [v2026.5.16~10] - 2026-05-17

_Generated from commits after `v2026.5.16~10`._
