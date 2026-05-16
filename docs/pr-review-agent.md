# Claude PR Review Agent

## Setup

1. Use Python 3.10 or newer.
2. From the repository root, run the command below.

```bash
python claude-review --pr https://github.com/owner/repo/pull/123
```

On Unix-like systems you can also make the wrapper executable and run:

```bash
chmod +x claude-review
./claude-review --pr https://github.com/owner/repo/pull/123
```

## Usage

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

For offline testing, pass a saved diff:

```bash
python claude-review --pr https://github.com/owner/repo/pull/123 --diff-file path/to/pr.diff
```

## Output format

The command prints a Markdown comment with:

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score: Low, Medium, or High

## Verification

```bash
python -m unittest tests.test_pr_review_agent
```
