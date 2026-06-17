# claude-review

A lightweight CLI tool and GitHub Action that reviews GitHub Pull Requests and produces structured Markdown output.

## Usage

```bash
# CLI
python claude-review.py --pr https://github.com/owner/repo/pull/123
python claude-review.py --pr https://github.com/owner/repo/pull/123 --token ghp_xxx
```

## What it does

- Fetches the PR diff via GitHub's API
- Analyzes: changed files, line counts, risky patterns (console.log, secrets, TODOs)
- Outputs a structured Markdown review with:
  - Summary of changes
  - Identified risks
  - Improvement suggestions
  - Confidence score

## Sample output

See the `samples/` directory for example reviews on real PRs.
