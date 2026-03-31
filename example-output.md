# 📊 Weekly Development Summary
**anthropics/anthropic-sdk-python** — Week of 2026-03-27

## Executive Summary

This week saw significant progress on the SDK with 23 commits from 5 contributors, focusing on streaming improvements, bug fixes, and documentation updates. Three major features were shipped, and 7 issues were resolved.

## Key Highlights

### 🚀 Features & Enhancements
- **Streaming overhaul** (#342): Refactored the streaming response handler to support Server-Sent Events (SSE) with automatic reconnection
- **Beta feature flag support** (#356): Added support for feature flags in beta API endpoints
- **Tool use improvements** (#361): Enhanced tool_use/tool_result handling with better error messages

### 🐛 Bug Fixes
- **Fixed rate limit retry logic** (#348): Resolved issue where exponential backoff wasn't being applied correctly
- **Fixed multipart upload timeout** (#352): Increased default timeout for large file uploads from 30s to 120s
- **Fixed content-type header** (#359): Corrected Content-Type for image analysis requests

### 📝 Documentation
- Updated Python SDK quickstart guide with latest API changes
- Added troubleshooting section for common streaming errors
- Improved code examples for tool use patterns

### 🔧 Maintenance
- Bumped dependency versions (httpx, pydantic)
- Added type hints for all new public methods
- CI pipeline improvements: added Python 3.13 to test matrix

## Breakdown by Category

| Category | Count |
|---|---|
| Features | 8 commits |
| Bug Fixes | 6 commits |
| Documentation | 4 commits |
| Maintenance | 5 commits |

## Contributors Spotlight

| Contributor | Commits | Focus |
|---|---|---|
| @dev-alice | 8 | Streaming, tool use |
| @dev-bob | 5 | Bug fixes |
| @dev-carol | 4 | Documentation |
| @dev-dave | 3 | CI/CD |
| @dev-eve | 3 | Type hints |

## Looking Ahead

- **Next week**: Batch API support, async generator improvements
- **In progress**: WebSocket streaming, enhanced error handling
- **On the radar**: v2.0 migration guide, breaking changes documentation

---
*Generated automatically by n8n + Claude API on 2026-03-27*
