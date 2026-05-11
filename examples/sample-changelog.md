# Changelog

## [1.2.0] - 2026-05-11

### Added
- User authentication with OAuth2 provider
- Dark mode support across all screens
- Real-time notification system

### Fixed
- Login crash on iOS 18 devices
- Memory leak in image cache layer
- Race condition in WebSocket reconnection

### Changed
- Bumped minimum deployment target from iOS 15 to iOS 17
- Refactored network layer for testability
- Upgraded dependencies to latest compatible versions

### Removed
- Deprecated v1 API support
- Legacy cookie-based session handling
- Obsolete localization files for deprecated markets
