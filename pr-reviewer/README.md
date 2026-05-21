# Claude PR Reviewer

A simple CLI tool powered by Claude Code (Anthropic API) that takes a Pull Request URL, analyzes the diff, and outputs a structured Markdown review comment.

## Features
Generates a structured review containing:
- Summary of changes (2-3 sentences)
- Identified risks (list)
- Improvement suggestions (list)
- Confidence score (Low / Medium / High)

## Setup

1. Install the tool:
```bash
pip install -e .
```

2. Set your Anthropic API key:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```
*(Optional) If you are reviewing private repositories, also set your GitHub token:*
```bash
export GITHUB_TOKEN="ghp_..."
```

## Usage

Run the CLI by passing a GitHub PR URL:
```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

The tool will fetch the PR diff directly from GitHub and output a high-quality Markdown review to your terminal.
