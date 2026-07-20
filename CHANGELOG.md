# Changelog

## [1.0.0] - 2026-07-13

### Added
- CLI tool for PR review (python3 claude_review.py --pr URL)
- GitHub Action workflow for auto-review
- Structured Markdown output (Summary, Risks, Suggestions, Confidence)
- Focus areas support (--focus security,performance)
- JSON output format
- Smart diff truncation (100k chars)
- Comment dedup (updates existing review)
- Sample outputs for 2 real PRs
- Automated tests (6 tests, all passing)
