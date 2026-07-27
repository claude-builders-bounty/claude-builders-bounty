# Claude PR Reviewer

A Claude Code sub-agent that takes a PR diff as input, analyzes it, and returns a structured Markdown review comment.

## Features

Generates a structured Markdown review including:
- Summary of changes (2–3 sentences)
- Identified risks (list)
- Improvement suggestions (list)
- Confidence score: Low / Medium / High

## Setup

1. Clone this repository.
2. Install the required dependencies:
   ```bash
   pip install .
   ```
3. Set your Anthropic API key in your environment variables:
   ```bash
   export ANTHROPIC_API_KEY="your-api-key-here"
   ```

## Usage

Run the `claude-review` CLI tool, passing the GitHub PR URL as an argument:

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

### Example

```bash
claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/139
```

This will output a structured Markdown review of the pull request changes.
