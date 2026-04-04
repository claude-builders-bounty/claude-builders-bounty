# Changelog

All notable changes to this project will be documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.1.0] — 2026-04-04
*(changes since v1.0.0)*

### Added
- add pagination support to /projects endpoint
- add full-text search across project records
- introduce email digest for weekly summary

### Fixed
- correct invoice total rounding error
- resolve null pointer when query is empty string

### Changed
- update button colors to match new brand guide
- improve error messages for failed webhook deliveries
- update API reference for new pagination params
- improve User model relationship mappings
- update GitHub Actions to ubuntu-latest

### Removed
- remove deprecated /v1/legacy-auth route