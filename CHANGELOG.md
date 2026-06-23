# Changelog

## [v0.1.0] - 2026-06-23

### Added
- Initial release of changelog generator script
- Support for parsing Conventional Commits prefixes
- Auto-categorization into Added/Fixed/Changed/Removed sections
- --since and --output command-line flags
- README with 3-step setup guide

### Fixed
- Handle repos with no git tags gracefully
- Skip merge commits in history