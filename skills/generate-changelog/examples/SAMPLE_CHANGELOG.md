# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v1.2.0] - 2026-11-01

### Added
- Claude Code automated PR review sub-agent with CLI & GitHub Action (`ba9785c`)
- n8n + Claude Code automated weekly dev summary workflow with Discord/Slack webhooks (`c70e639`)
- Pre-tool-use security hook blocking destructive bash commands (`9b3f12a`)

### Fixed
- ANSI color bleeding across Windows PowerShell terminal environments (`7a1c890`)
- Subprocess deadlocks when stream pipe buffers saturate under heavy concurrency (`3c5e219`)

### Changed
- Refactored AST token extraction pipeline for 3x throughput improvement (`2e9f140`)
- Upgraded CI runners to Node.js 22 and Python 3.12 (`1b4d088`)

### Security
- Blocked recursive root removals and shell piping attacks in PreToolUse hook (`8f9c001`)

## [v1.1.0] - 2026-10-24

### Added
- Initial community bounty board repository (`1aeae2a`)
- Automated Opire bounty claim webhook handler (`a80a580`)
