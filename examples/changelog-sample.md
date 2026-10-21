# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2026-10-21

### Added
- Add support for Python 3.14 and drop support for Python 3.8 (#6993) (2edca11)
- Add Trusted Publishing Release Workflow (e57b5bf)

### Fixed
- Fix typo in documentation for verify (3f07f99)

### Changed
- Update publish workflow to use `artifact-id` instead of `name` (46e939b)
- Update Makefile rules (#6996) (fec96cd)

### Documentation
- clarify timeout parameter uses seconds in Session.request (#6994) (d58d8aa)

### Other Changes
- v2.32.5 (b25c87d)
- Merge pull request #7010 from psf/dependabot/github_actions/actions/checkout-5.0.0 (131e506)
- Bump actions/checkout from 4.2.0 to 5.0.0 (b336cb2)
- Merge pull request #6999 from psf/dependabot/github_actions/step-security/harden-runner-2.13.0 (4b9c546)
- Bump step-security/harden-runner from 2.12.0 to 2.13.0 (7618dbe)
- Bump github/codeql-action from 3.28.5 to 3.29.0 (91a3eab)
- Revert caching a default SSLContext (#6767) (90fee08)
- Clarify error description in cloning instructions (8ff173b)
