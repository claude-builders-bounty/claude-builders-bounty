# Changelog

## [Unreleased] - 2026-05-20

### Added

- Add sample preview for non-admin users
- Forex + derivatives + defi + weekly recap (v3.5+)
- Inline keyboards + signal accuracy tracking (v3.5)
- Docs: rewrite README for v3.5 - full architecture, new features, roadmap
- Major upgrade - AI quality, monetization, UX, scalability
- Enhance alert system with multi-stage notifications and update WIB time calculation
- Implement broadcast system for alert subscriptions and high impact events
- Update economic calendar handler to fetch high impact events from Finnhub
- Add Telegram News Collector and Authentication System
- Enhance Telegram bot with improved data collection and logging
- Add SwiftRouter API configuration to settings

### Changed

- Refactor requirements and enhance test coverage
- Refactor DeepSeek API configuration for consistency and clarity
- Enhance AI report generator with 9Router integration and update configuration settings
- Update AI report generator to v4.0 with SwiftRouter integration and improved fallback handling
- First commit

### Fixed

- Fix callback auth + improve /start UX for non-admin users
- Fix forex change and accuracy price extraction
- Escape markdown in dynamic AI reasoning, add /alert commands to /help
- Timezone WIB, memory leak, security, performance, systemd

### Removed

- Remove redundant check for swiftrouter API key in settings
