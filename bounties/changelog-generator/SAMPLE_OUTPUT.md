# Changelog

All notable changes to this project will be documented in this file.

## [v2.1.0] - 2026-05-16

### Added
- feat: Add dark mode toggle to settings panel
- feat: Implement user notification preferences
- new: Create onboarding wizard for new users
- add: Support for WebP image uploads

### Fixed
- fix: Resolve memory leak in WebSocket connection handler
- fix: Correct timezone display in user profiles
- bugfix: Address race condition in concurrent file uploads

### Changed
- refactor: Migrate authentication to JWT tokens
- update: Bump dependencies to latest versions
- docs: Improve API endpoint documentation
- chore: Reorganize project folder structure

### Removed
- remove: Drop legacy API v1 endpoints
- deprecate: Remove support for IE11
