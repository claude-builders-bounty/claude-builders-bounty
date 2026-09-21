# PR Reviewer Agent

Automatically review pull requests and produce structured Markdown output with code quality assessment, security concerns, test coverage check, and suggested improvements.

## What it does

1. Fetches PR metadata and diff via GitHub API / `gh` CLI
2. Parses the exact unified patch for security patterns, test coverage, documentation updates, and generated/vendor uncertainty
3. Generates a structured Markdown report with Summary, Code Quality, Security, Tests, Documentation, Suggestions, and Confidence
4. Posts the report as a PR comment only when explicitly enabled in the GitHub Action

## Installation

### As a GitHub Action

```yaml
name: PR Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - name: PR Review
        uses: your-org/claude-builders-bounty/skills/pr-reviewer@main
        with:
          pr_number: ${{ github.event.pull_request.number }}
```

### As a CLI tool

The CLI accepts a real GitHub PR URL, fetches metadata and the diff with `gh` when available or GitHub's unauthenticated API, and writes the review without posting anything:

Requirements: Python 3.10 or newer. The CLI has no third-party Python dependencies. An authenticated `gh` installation is optional but recommended to avoid GitHub's low unauthenticated API rate limit.

```bash
python3 skills/pr-reviewer/scripts/generate_review.py \\
  --pr https://github.com/owner/repo/pull/123 \\
  --output report.md
```

Run the command from the repository root (the path above is root-relative). It uses `gh` when available and otherwise reads public PR metadata/diffs through GitHub's unauthenticated API; no token or secret is written to reports. Invalid or inaccessible PRs and malformed local inputs fail cleanly without a traceback. The patch is authoritative for changed files and line counts; every unified-diff hunk must have matching declared and observed old/new line counts and reviewable text patches must include matching, canonical `---`/`+++` paths.

The report deliberately distinguishes four input states:

- **Valid:** structurally complete textual changes produce a grounded review.
- **Insufficient:** empty or trivial changes produce an explicit no-review result.
- **Limited:** binary/uninspectable files or incomplete metadata are named explicitly, confidence is Low, and no security conclusion is made for uninspected content. A binary-only patch does not receive a normal review.
- **Rejected:** unsafe paths, conflicting/duplicate headers, malformed hunks, repeated file sections, or binary/text structure mixed within one file produce a rejection report and exit status 2.

Missing or mismatched metadata is always surfaced as uncertainty rather than silently treated as fact. Binary files can coexist with valid textual files, but every uninspectable path is listed and the result remains a limited review requiring manual inspection. `GIT binary patch` payloads are structurally validated (literal/delta framing, base85 line lengths, and declared byte totals); truncated, malformed, or binary/text-mixed sections are rejected rather than downgraded to a limited review.

For offline/reproducible runs, metadata and diff files are also supported. Capture those inputs from the public PR at a pinned revision and commit only sanitized fixtures; never commit credentials:

```bash
python3 skills/pr-reviewer/scripts/generate_review.py --metadata pr_metadata.json --diff pr_diff.patch -o report.md
```

The GitHub Action accepts workspace-relative `output_file` paths (including nested paths), and rejects absolute paths, `..` escapes, and symlink escapes before writing or uploading a report. Shell arguments are passed through environment variables and quoting; posting remains opt-in.

For exact-candidate audit artifacts, optionally bind the report to `--candidate-sha`, `--worktree`, `--clean`, `--evidence-for-sha`, and `--audit-for-sha`. These values are recorded as evidence labels; they are not inferred or treated as proof by the reviewer.

## Example Output

```markdown
## PR Review Report

### 📋 Summary
- **PR:** Add user authentication
- **Files changed:** 8 (342 lines added, 45 removed)
- **Overall assessment:** ⚠️ Needs revision before merge

### ✅ Code Quality
- 8 files changed — reasonable scope
- 342 lines added — manageable size

### 🔒 Security
- ❌ **Hardcoded credential** in `src/auth.py`: `password = "secret123"`

### 🧪 Tests
- ✅ Test files included in this PR

### 📖 Documentation
- ⚠️ No documentation changes detected

### 💡 Suggestions
1. Address 1 security flag(s) identified above
2. Update documentation for any public API changes
```

## Acceptance Criteria

- [x] Works via GitHub Action (`action.yml`)
- [x] Works via CLI (`python3 skills/pr-reviewer/scripts/generate_review.py --pr <URL>`)
- [x] Structured Markdown output with Summary, Code Quality, Security, Tests, Documentation, Suggestions, and Confidence
- [x] Executed against 2 real public PR URLs; captured outputs are in `tests/real_outputs/`
- [x] README with setup instructions

The Python tests import and exercise `generate_review.py` directly, including patch-grounded counts, partial metadata, deletion-heavy and large changes, docs-only examples, tests-only changes, security findings, malformed/inaccessible input, binary/generated paths, confidence gating, evidence binding, and empty/trivial input. The files in `tests/real_outputs/` are checked-in outputs from the real CLI against public PR URLs; regenerate them only from those public inputs and inspect that no secrets are present.

Real-output fixtures:

- `tests/real_outputs/cli-14481.md` ← https://github.com/cli/cli/pull/14481 (empty-diff no-review case)
- `tests/real_outputs/cli-14478.md` ← https://github.com/cli/cli/pull/14478

## Files

- `action.yml` — GitHub Action definition
- `pr-reviewer-skill.md` — Agent skill definition (Claude Code / OpenClaw)
- `scripts/generate_review.py` — CLI implementation
- `tests/test_pr_reviewer.py` — Test suite
- `README.md` — This file
