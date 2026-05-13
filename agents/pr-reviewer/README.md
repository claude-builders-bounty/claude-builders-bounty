# Claude PR Reviewer Agent

A dependency-free PR review agent for bounty #4. It accepts either a GitHub PR URL or a local unified diff and returns a structured Markdown review comment with the required sections. The default path is deterministic static analysis; an optional external LLM command can be used when you want Claude or another model to write the review text from the same prompt contract.

## Bounty Checklist

- CLI: `claude-review --pr https://github.com/owner/repo/pull/123`
- GitHub Action workflow: `github-action.yml`
- Structured Markdown: Summary, Identified Risks, Improvement Suggestions, Confidence Score
- Real PR samples: `samples/`
- Setup and usage docs: this README
- Tests: `python -m unittest discover -s agents/pr-reviewer/tests`

Additional hardening is included without requiring API keys: structured findings, dependency-impact checks, test relevance checks, JSON/SARIF output, annotations, and optional LLM handoff.

## Setup

1. Use Python 3.10 or newer.
2. Install the CLI from this directory:

```bash
cd agents/pr-reviewer
python -m pip install -e .
```

3. Optional: install and authenticate the GitHub CLI with `gh auth login` for private repositories. Public PRs can also be fetched through the GitHub REST API.

## Usage

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

The shorthand form also works:

```bash
claude-review --pr owner/repo#123
```

Review a local diff:

```bash
claude-review --diff-file tests/fixtures/security.diff
```

Emit machine-readable JSON, including structured findings:

```bash
claude-review --diff-file tests/fixtures/security.diff --format json
```

Emit SARIF for code-scanning style tooling:

```bash
claude-review --pr owner/repo#123 --format sarif --output claude-review.sarif
```

Scan a local checkout for downstream references to changed functions/classes/exports:

```bash
claude-review --diff-file pr.diff --repo-root /path/to/checkout
```

Use a project config:

```bash
claude-review --pr owner/repo#123 --config .claude-review.yml
```

Write the review to a file:

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

Post the review as a GitHub PR comment:

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --post-comment
```

Update the previous generated comment instead of adding a new one on every run:

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --update-comment
```

`--post-comment` and `--update-comment` require the GitHub CLI because they intentionally reuse the user's existing authenticated GitHub setup instead of managing tokens directly.

For GitHub Actions, emit file/line annotations and a job summary in addition to the PR comment:

```bash
claude-review \
  --pr https://github.com/owner/repo/pull/123 \
  --repo-root "$GITHUB_WORKSPACE" \
  --github-annotations \
  --step-summary \
  --allow-comment-failure \
  --update-comment
```

`--allow-comment-failure` is useful on fork PRs where GitHub may make `GITHUB_TOKEN` read-only. In that case the job can still show annotations and the step summary even if the PR comment cannot be written.

Optionally fail the command after writing the review when findings meet a severity threshold:

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --fail-on High
```

`--fail-on High` fails only for high-severity findings. `--fail-on Medium` fails for medium or high findings. The default is non-blocking, which is safer for advisory PR comments.

Use an external LLM backend by passing a command. The prompt is written to stdin and the command must return JSON with `summary`, `risks`, `suggestions`, and `confidence`:

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --llm-command "claude -p"
```

When `--llm-command` is used, deterministic findings are still merged into the final risks and suggestions so model output cannot accidentally drop static safety checks. The final confidence score also keeps the more conservative value between the LLM response and deterministic analysis.

Inspect the exact prompt without calling a model:

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --prompt-only
```

From a source checkout, this compatibility form also works without installation:

```bash
python agents/pr-reviewer/claude-review.py --pr https://github.com/owner/repo/pull/123
```

## Output Contract

The Markdown output always contains these headings:

```markdown
## Claude Code PR Review

### Review Metadata
### Summary
### Identified Risks
### Improvement Suggestions
### Confidence Score
```

Default risk bullets use this shape:

```text
[High][RULE_CODE] path/to/file.py:42 - Message. Evidence: `changed line`.
```

JSON output contains the same review fields plus a `findings` array:

```json
{
  "summary": "...",
  "risks": ["..."],
  "suggestions": ["..."],
  "confidence": "Medium",
  "findings": [
    {
      "code": "SHELL_TRUE",
      "severity": "High",
      "path": "app/auth.py",
      "line": 5,
      "message": "...",
      "suggestion": "...",
      "evidence": "subprocess.run(...)"
    }
  ]
}
```

SARIF output uses SARIF 2.1.0 and maps severities as `High -> error`, `Medium -> warning`, and `Low -> note`.

The confidence score is deterministic:

- `High` for small diffs with tests and no high-risk patterns.
- `Medium` for missing tests, moderate size, dependency-impact findings, or specific risky constructs.
- `Low` for truncated, very large, or very broad diffs.

Empty diffs are rejected. `--max-diff-chars` defaults to `500000` and must be at least `1000` so the parser has enough context to identify files and changed lines.

Dependency analysis has two modes:

- Diff-local mode always runs. It tracks changed Python, JavaScript/TypeScript, Go, Rust, class, export, and constant symbols visible in the unified diff, then flags non-test changed callers that reference those symbols.
- Repo-root mode runs only with `--repo-root`. It scans a bounded set of source files in the local checkout, skips common generated/vendor directories, prefers real use sites over import-only lines, and flags non-test references outside the PR diff.
- Test relevance mode checks whether changed test lines mention changed symbols from existing non-test files. It avoids flooding all-new packages with one finding per helper, but still emits `CHANGED_SYMBOL_WITHOUT_RELEVANT_TEST` when an existing changed symbol appears to be paired with unrelated test edits.

Runtime-risk rules focus on non-test source/config/script paths and skip tests, documentation, fixtures, examples, and generated sample reports by default. This keeps deliberately dangerous test fixtures and saved review outputs from being reported as live production risks.

GitHub Actions integration can emit `::warning` annotations for located findings. Global findings such as missing tests remain in the review body and step summary rather than being attached to an arbitrary file.

## Configuration

By default, the CLI auto-detects `.claude-review.yml`, `.claude-review.yaml`, or `.claude-review.json` in `--repo-root` and then the current directory. Use `--config` to point at a specific file.

YAML support is intentionally a small dependency-free subset: top-level lists and simple key/value maps only. Use JSON if your project needs a more complex config shape.

Supported fields:

```yaml
disabled_rules:
  - TODO_IN_CHANGE

ignored_paths:
  - docs/**
  - generated/**

severity_overrides:
  DEPENDENCY_CHANGE: Low
```

See `.claude-review.example.yml` for a starter config.

## GitHub Action

`github-action.yml` is a copyable workflow example. It assumes this package is committed at `agents/pr-reviewer`, installs it with `python -m pip install ./agents/pr-reviewer`, and calls the installed `claude-review` command. Place it at `.github/workflows/claude-review.yml` in the target repository if you want automatic review comments on opened or updated PRs.

The workflow uses `--update-comment`, so pushes to the same PR edit the prior generated review comment instead of posting a new full review each time.

It also passes `--repo-root "${GITHUB_WORKSPACE}"`, which enables reverse-reference scanning inside the checked-out repository. That allows the reviewer to flag changed symbols that are referenced by non-test files outside the PR diff.

The workflow emits GitHub warning annotations and appends the Markdown review to the job step summary. It also uses `--allow-comment-failure`, because GitHub's `pull_request` workflows can receive read-only tokens on fork PRs; the review should still be visible even when the top-level comment is rejected.

This directory also includes `action.yml`, so the reviewer can be used as a local composite action:

```yaml
- uses: ./agents/pr-reviewer
  with:
    pr: ${{ github.event.pull_request.html_url }}
    token: ${{ secrets.GITHUB_TOKEN }}
    fail-on: High
```

The `fail-on` action input is optional. Leave it empty for a non-blocking reviewer, or set it to `High`, `Medium`, or `Low` when you want findings at that level or above to fail the workflow after the comment, annotations, and step summary are written.

`github-action-sarif.yml` is an optional workflow that writes `claude-review.sarif` and uploads it with `github/codeql-action/upload-sarif@v3`. Use it when you want findings to appear in GitHub code scanning instead of, or in addition to, PR comments.

## Claude Code Agent Usage

`SKILL.md` provides a Claude Code agent instruction wrapper for this CLI. The agent flow is intentionally deterministic and offline-friendly: Claude Code can invoke `claude-review --pr ...` for a public or authenticated GitHub PR, or `claude-review --diff-file ...` for a local diff without any network call.

## Verification

```bash
python -m unittest discover -s agents/pr-reviewer/tests
python agents/pr-reviewer/claude-review.py --diff-file agents/pr-reviewer/tests/fixtures/security.diff
python agents/pr-reviewer/claude-review.py --diff-file agents/pr-reviewer/tests/fixtures/security.diff --format json
python agents/pr-reviewer/claude-review.py --diff-file agents/pr-reviewer/tests/fixtures/dependency_impact.diff --format sarif
python agents/pr-reviewer/claude-review.py --diff-file agents/pr-reviewer/tests/fixtures/dependency_impact.diff
python agents/pr-reviewer/claude-review.py --diff-file agents/pr-reviewer/tests/fixtures/dependency_impact.diff --github-annotations --step-summary /tmp/claude-review-summary.md
python agents/pr-reviewer/claude-review.py --diff-file agents/pr-reviewer/tests/fixtures/security.diff --prompt-only
cd agents/pr-reviewer && python -m pip install -e . && claude-review --diff-file tests/fixtures/security.diff
```

Verified locally on 2026-05-13:

```text
python -m unittest discover -s agents/pr-reviewer/tests
Ran 30 tests - OK

python -m py_compile agents/pr-reviewer/claude-review.py agents/pr-reviewer/claude_review/cli.py agents/pr-reviewer/tests/test_claude_review.py
passed
```

Sample outputs from real public PRs are in `samples/`. Regenerate the current set with:

```bash
claude-review --pr https://github.com/psf/requests/pull/7310 --no-gh --output samples/psf-requests-7310.md
claude-review --pr https://github.com/pallets/flask/pull/6018 --no-gh --output samples/pallets-flask-6018.md
claude-review --pr https://github.com/vercel/next.js/pull/93794 --no-gh --output samples/vercel-nextjs-93794.md
```
