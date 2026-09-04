# feat(agent): Claude Code sub-agent PR review with structured output (#4)

Fixes #4 (💰 **Bounty: $150**)

## Technical Diagnosis & Summary

Code reviews are a vital line of defense in modern software development. Without an automated, reliable review agent, pull requests often suffer from delayed feedback cycles, overlooked security pitfalls (e.g. hardcoded credentials, command injection via `shell=True`), and inadequate test coverage.

This pull request implements a zero-dependency, cross-platform Claude Code PR Review Agent capable of analyzing pull request diffs, assessing security and stability risks, recommending actionable improvements, and outputting structured Markdown reviews both via CLI and via GitHub Actions.

---

## Acceptance Criteria Checklist

- [x] **Works via CLI**: `claude-review --pr https://github.com/owner/repo/pull/123` (or `python3 claude_review.py --pr ...`)
- [x] **Works via GitHub Action**: Included in `.github/workflows/claude-pr-review.yml`
- [x] **Structured Markdown output** with:
  - **Summary of changes** (2–3 sentences)
  - **Identified risks** (bulleted list)
  - **Improvement suggestions** (bulleted list)
  - **Confidence score**: Low / Medium / High with justification
- [x] **Tested on at least 2 real GitHub PRs**: Sample outputs included in `sample-outputs/pr-4080.md` and `sample-outputs/pr-4081.md`
- [x] **README with setup and usage instructions**

---

## Deliverables in This PR

- `claude_review.py`: The cross-platform CLI review agent with Anthropic API, Claude CLI, and heuristic diff analysis fallback engines.
- `claude-review`: Executable wrapper for Unix/macOS environments.
- `.github/workflows/claude-pr-review.yml`: Automated CI workflow for pull requests with automatic comment posting.
- `sample-outputs/pr-4080.md`: Real output from reviewing PR #4080 (`feat: add changelog generator skill from git history`).
- `sample-outputs/pr-4081.md`: Real output from reviewing PR #4081 (`feat(hooks): pre-tool-use hook to block destructive bash commands`).
- `agents/pr-reviewer/README.md`: Setup, CLI options, GitHub Actions configuration, and usage guide.
- `tests/test_claude_review.py`: 9-test unit and integration test suite covering URL parsing, diff analysis, output formatting, and CLI execution.

---

## Usage Examples

```bash
# Basic review to stdout
./claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/4080

# Output to Markdown file
python3 claude_review.py --pr https://github.com/owner/repo/pull/123 --output review.md

# Automatically post review comment directly onto GitHub PR
python3 claude_review.py --pr https://github.com/owner/repo/pull/123 --post
```

---

## Test Execution Results

Command: `python -m unittest discover -s tests -p "test_claude_review.py" -v`

```text
test_diff_mode_cli (test_claude_review.TestCliExecution.test_diff_mode_cli) ... ok
test_confidence_score_values (test_claude_review.TestReviewFormatting.test_confidence_score_values) ... ok
test_format_full_markdown_header (test_claude_review.TestReviewFormatting.test_format_full_markdown_header) ... ok
test_review_sections_exist (test_claude_review.TestReviewFormatting.test_review_sections_exist) ... ok
test_invalid_url_raises_error (test_claude_review.TestUrlParsing.test_invalid_url_raises_error) ... ok
test_number_with_repo_override (test_claude_review.TestUrlParsing.test_number_with_repo_override) ... ok
test_number_without_repo_raises_error (test_claude_review.TestUrlParsing.test_number_without_repo_raises_error) ... ok
test_short_domain_url (test_claude_review.TestUrlParsing.test_short_domain_url) ... ok
test_standard_https_url (test_claude_review.TestUrlParsing.test_standard_https_url) ... ok

----------------------------------------------------------------------
Ran 9 tests in 0.113s

OK
```

---

Closes #4
