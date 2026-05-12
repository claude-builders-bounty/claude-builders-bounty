# PR review agent (Issue #4 submission)

This submission provides a CLI tool that reviews a GitHub pull request diff and outputs a structured Markdown review.

## Deliverables

- `claude-review` executable CLI
- `claude_review.py` analyzer
- Offline verification fixtures and sample output files

## Setup

```bash
cd pr-review-agent
chmod +x ./claude-review
```

## Usage

Online mode (fetches `<PR_URL>.diff`):

```bash
./claude-review --pr https://github.com/OWNER/REPO/pull/123
```

Write to file:

```bash
./claude-review --pr https://github.com/OWNER/REPO/pull/123 --output review.md
```

Offline mode (used in this repo because sandbox networking cannot resolve GitHub):

```bash
./claude-review --pr https://github.com/example-org/example-repo/pull/101 \
  --diff-file fixtures/sample_pr_1.diff \
  --output sample-output/review-pr-101.md
```

## Output format

The generated Markdown always includes:

- `## Summary`
- `## Identified Risks`
- `## Improvement Suggestions`
- `## Confidence Score`

## Verification run (2 PR fixtures)

```bash
./claude-review --pr https://github.com/example-org/example-repo/pull/101 \
  --diff-file fixtures/sample_pr_1.diff \
  --output sample-output/review-pr-101.md

./claude-review --pr https://github.com/example-org/example-repo/pull/202 \
  --diff-file fixtures/sample_pr_2.diff \
  --output sample-output/review-pr-202.md
```

The resulting output files are committed under `sample-output/`.

## Live PR test note

This sandbox cannot resolve `github.com`, so live fetch tests (`--pr` without `--diff-file`) are blocked in this environment. The command below is ready for a human-approved rerun in a networked environment:

```bash
./claude-review --pr https://github.com/OWNER/REPO/pull/123 --output review.md
```

## Acceptance criteria mapping

- Works via CLI command: `claude-review --pr ...`
- Takes PR diff as input: fetches from `<PR_URL>.diff` or accepts `--diff-file` fallback
- Structured Markdown output: Summary, Identified Risks, Improvement Suggestions, Confidence Score
- Includes setup and usage docs
- Includes two sample review outputs generated from diff inputs
