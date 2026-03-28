# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2026-03-27

### Added
- Add all products, CI/CD pipeline, and landing page
- Add Hooks Pack product, SEO blog post, updated distribution links
- Add individual product landing pages + fix payment link swap bug
- Add smoke tests, email inbox worker, and security fixes
- Download auth + price increase + security hardening
- Stripe test mode for preview environment

### Fixed
- Add ENVIRONMENT vars to wrangler config for both envs
- Specify explicit deploy command for wrangler v4 multi-env
- Use npm as packageManager (not npx)
- Use wrangler v4 in CI and rename config to .json

### Changed
- First commit
- Trigger CI/CD pipeline test
- Verify CI/CD preview deploy

---

*Generated from [zerodaykit/earn](https://github.com/mattfo0/earn) (13 commits, full history, no tags found).*

*Tool: `changelog.sh --stdout` and `/generate-changelog` Claude Code skill.*
