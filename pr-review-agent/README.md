# Claude PR Review Agent

A CLI tool that analyzes GitHub PR diffs and returns a structured Markdown review.

## Requirements

- Python 3.9+

## Installation

```bash
pip install claude-review
```

Or run directly:

```bash
python claude-review --pr https://github.com/owner/repo/pull/123
```

## Usage

```bash
# Review a PR (output to stdout)
python claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2774

# Save review to file
python claude-review --pr https://github.com/owner/repo/pull/123 -o review.md

# Use with Claude Code
claude code --tool "python claude-review --pr https://github.com/owner/repo/pull/123"
```

## Output Structure

The review includes:

| Section | Description |
|---------|-------------|
| **Summary** | 2–3 sentences describing the change scope |
| **Identified Risks** | Dependency changes, deleted files, schema changes, sensitive files |
| **Improvement Suggestions** | TODOs, FIXMEs, large files, debug prints, lint suppressions |
| **Confidence Score** | High / Medium / Low based on PR size and complexity |
| **Changed Files** | Table with file, status, additions/deletions, category |

## Examples

See the `examples/` directory for sample outputs from real PRs.

## How It Works

1. Fetches PR metadata and file diff from the GitHub API
2. Classifies each file by type (code, test, docs, config, dependencies)
3. Scans for risk indicators and improvement opportunities
4. Generates structured Markdown output
