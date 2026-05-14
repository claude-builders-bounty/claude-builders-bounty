# Claude Code PR Review Agent

**Bounty:** #4 — $150 (Opire)

A CLI tool that analyzes GitHub pull requests and generates structured Markdown reviews.

## Quick Start

```bash
# 1. Install (single file, no dependencies beyond Python 3)
chmod +x pr-review-agent/claude-review

# 2. Review any PR
export GITHUB_TOKEN=your_github_token
./pr-review-agent/claude-review --pr https://github.com/owner/repo/pull/123
```

## Features

- Fetches PR diff and metadata via GitHub API
- Analyzes file changes, diff hunks, and code patterns
- Detects risks: large PRs, massive hunks, dependency changes
- Suggests improvements: missing tests, oversized modifications
- Outputs structured Markdown with confidence scoring
- No external dependencies — pure Python 3 stdlib

## Output Structure

```
## PR Review: owner/repo#123
- Summary of Changes (2-3 sentence overview)
- Changes Overview (files, additions, deletions, file types)
- Identified Risks (list with explanations)
- Improvement Suggestions (actionable list)
- Confidence Score (Low / Medium / High)
```

## Usage

```bash
# Review and print to stdout
./claude-review --pr https://github.com/owner/repo/pull/123

# Review and save to file
./claude-review --pr https://github.com/owner/repo/pull/123 --output review.md

# With explicit token
./claude-review --pr https://github.com/owner/repo/pull/123 --token ghp_xxx
```

## How It Works

1. Parses the PR URL to extract owner, repo, and PR number
2. Fetches PR metadata and file list via GitHub REST API
3. Downloads the unified diff for full analysis
4. Analyzes: file types, hunk sizes, risky patterns, missing tests
5. Generates structured Markdown output with summary, risks, suggestions, and confidence

## Sample Outputs

See `examples/` directory for reviews of real PRs:
- `review-example-1.md` — PR #1281: Pre-tool-use hook (161 additions, 2 files)
- `review-example-2.md` — PR #1280: n8n workflow (361 additions, 2 files)

## Requirements

- Python 3.8+
- GitHub token with `repo` scope
