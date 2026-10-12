# Claude Code PR Reviewer Sub-Agent

A dedicated PR reviewer agent designed for Claude Code and automated CI/CD pipelines. It inspects unified git diffs, analyzes structural changes, identifies security risks (destructive operations, hardcoded secrets, dangerous commands), checks test coverage, and generates structured Markdown review comments with actionable feedback and confidence scores.

## Features

- **Dual Execution Modes**:
  - **CLI**: Direct terminal usage with `--pr <url>` or piping unified diffs.
  - **GitHub Action**: Ready-to-use composite action for continuous PR gating.
- **Deep Static Diff Analysis**:
  - Detects destructive bash operations (`rm -rf`, `mkfs`).
  - Detects destructive SQL operations (`DROP TABLE`, `TRUNCATE`).
  - Flags sensitive credential leaks (`api_key`, `ghp_...`, `sk-...`).
  - Checks for test presence when modifying executable code.
  - Monitors diff scale and cognitive review load.
- **Structured Markdown Output**:
  - Summary of changes (2–3 sentences)
  - Identified risks (bulleted list)
  - Improvement suggestions (bulleted list)
  - Confidence score: `High` / `Medium` / `Low` with explicit rationale
- **Automated PR Posting**: Optionally posts the review directly as a PR comment when `--post-comment` and `GITHUB_TOKEN` are provided.

---

## Quick Start (CLI)

### 1. Direct Python Execution
```bash
python agents/pr-reviewer/claude_review.py --pr https://github.com/owner/repo/pull/123
```

### 2. Using the CLI wrapper
```bash
./bin/claude-review --pr https://github.com/owner/repo/pull/123
```

### 3. Reviewing Local Diffs or Pipes
```bash
git diff main | python agents/pr-reviewer/claude_review.py
# or
python agents/pr-reviewer/claude_review.py --diff-file path/to/patch.diff
```

### 4. Reviewing Private PRs & Posting Comments
```bash
export GITHUB_TOKEN="ghp_your_token_here"
python agents/pr-reviewer/claude_review.py \
  --pr https://github.com/owner/repo/pull/123 \
  --post-comment
```

---

## GitHub Action Integration

Add the workflow file `.github/workflows/pr-review.yml` to your repository:

```yaml
name: Claude PR Reviewer

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write
  issues: write

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Run Claude PR Reviewer
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python agents/pr-reviewer/claude_review.py \
            --pr "${{ github.event.pull_request.html_url }}" \
            --post-comment
```

---

## Verified Real-World PR Test Outputs

The reviewer was tested on two real production GitHub PRs:

1. **[Sample Review #1](examples/sample_review_pr1.md)**: Tested on PR `#4786` (Destructive Command Blocker Hook).
   - Accurately flagged destructive command strings (`rm -rf`, `DROP TABLE`) embedded in the test/regex definitions.
   - Assigned `Low` confidence due to elevated sensitivity, prompting manual review.
2. **[Sample Review #2](examples/sample_review_pr2.md)**: Tested on PR `#4787` (Structured CHANGELOG Generator Skill).
   - Confirmed clean change set with unit tests present and zero credential leaks.
   - Assigned `High` confidence score.

---

## Running Unit Tests

Run the test suite with standard Python `unittest`:

```bash
python -m unittest agents/pr-reviewer/tests/test_reviewer.py
```
Expected output:
```
......
----------------------------------------------------------------------
Ran 6 tests in 0.001s

OK
```
