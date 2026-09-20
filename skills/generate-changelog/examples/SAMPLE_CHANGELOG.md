# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v1.2.0] - 2026-09-20

### Added
- Multi-asset escrow routing for XLM and USDC tokens ([`7f2a1b9`] - @rushikeshgarad2024-dev)
- Automatic webhook verification for pull request merge events ([`8c3d4e5`] - @priyaeth)
- Real-time ledger horizon stream listener for contract invocations ([`9d4e5f6`] - @0xkoda)

### Fixed
- Reconnect race condition on testnet wallet network switch ([`4a1b2c3`] - @devrel_ana)
- Stale KYC token verification header in HTTP request interceptor ([`5b2c3d4`] - @rushikeshgarad2024-dev)
- Missing `Permissions-Policy` response header in Next.js edge configuration ([`6c3d4e5`] - @rushikeshgarad2024-dev)

### Changed
- Refactor pipeline board state management to use React query cache ([`1a2b3c4`] - @priyaeth)
- Pinned all GitHub Action runners in CI workflows to full commit SHAs ([`2b3c4d5`] - @rushikeshgarad2024-dev)
- Update dependencies to Node 22 LTS compatibility ([`3c4d5e6`] - @devrel_ana)

### Removed
- Deprecated legacy v1 escrow RPC polling adapter ([`0f1e2d3`] - @0xkoda)
- Remove unused JWT session fallback cookie handler ([`1e2d3c4`] - @rushikeshgarad2024-dev)
