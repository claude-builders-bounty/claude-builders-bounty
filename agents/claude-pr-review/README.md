# Claude PR Review Agent

`claude-review` is a dependency-free Claude Code companion for reviewing GitHub pull requests. It fetches a PR diff, analyzes changed lines, and returns a structured Markdown comment with the sections required by bounty #4.

## Features

- CLI: `./claude-review --pr https://github.com/owner/repo/pull/123`
- Local diff mode: `./claude-review --diff-file change.diff`
- Optional `--comment` mode posts the generated review back to the PR
- GitHub Action workflow YAML included at `agents/claude-pr-review/github-action/claude-pr-review.yml`
- Structured output:
  - Summary of Changes
  - Identified Risks
  - Improvement Suggestions
  - Confidence Score: Low / Medium / High
- No runtime dependencies beyond Python 3.10+
- Unit tests for URL parsing, required output sections, risk detection, and confidence scoring

## Setup

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
cd claude-builders-bounty
chmod +x claude-review agents/claude-pr-review/claude_review.py
```

For public repositories, unauthenticated GitHub API access may work. Set `GITHUB_TOKEN` to avoid rate limits or to post comments:

```bash
export GITHUB_TOKEN=ghp_your_token
```

## Usage

Review a PR and print Markdown:

```bash
./claude-review --pr https://github.com/owner/repo/pull/123
```

Use an owner/repo pair plus number:

```bash
./claude-review --repo owner/repo --pr-number 123
```

Write the review to a file:

```bash
./claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

Analyze a local diff:

```bash
git diff main...HEAD > change.diff
./claude-review --diff-file change.diff --title "Local patch"
```

Post the review as a pull request comment:

```bash
GITHUB_TOKEN=ghp_your_token ./claude-review \
  --pr https://github.com/owner/repo/pull/123 \
  --comment
```

## GitHub Action

The included workflow runs on pull requests and posts a structured review comment using the repository `GITHUB_TOKEN`. Copy `agents/claude-pr-review/github-action/claude-pr-review.yml` into `.github/workflows/claude-pr-review.yml` to enable it in a repository.

```yaml
name: Claude PR Review

on:
  pull_request_target:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: read
  issues: write

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: ./claude-review --pr "$PR_URL" --comment
        env:
          PR_URL: ${{ github.event.pull_request.html_url }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

The workflow does not check out or execute code from the pull request branch.

## Verification

Run the unit tests:

```bash
python3 -m unittest discover -s agents/claude-pr-review/tests
```

Compile the CLI:

```bash
python3 -m py_compile agents/claude-pr-review/claude_review.py
```

Generate the included real-PR samples:

```bash
./claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/1537 --output agents/claude-pr-review/samples/claude-builders-bounty-1537.md
./claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/1509 --output agents/claude-pr-review/samples/claude-builders-bounty-1509.md
```
