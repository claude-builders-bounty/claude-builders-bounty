# claude-review

An AI-powered GitHub PR reviewer that fetches a pull request diff and produces a structured Markdown code review using Claude.

## Requirements

- Python 3.10+
- `requests` library
- `anthropic` Python SDK
- An Anthropic API key ([get one here](https://console.anthropic.com/))
- A GitHub token (optional, required for private repos)

## Installation

```bash
# Install dependencies
pip install requests anthropic

# Make the script executable (macOS/Linux)
chmod +x claude_review.py

# Optional: add to PATH for global use
ln -s "$(pwd)/claude_review.py" /usr/local/bin/claude-review
```

## Configuration

Set the required environment variables:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."          # Required
export GITHUB_TOKEN="ghp_..."                  # Optional (needed for private repos)
```

Add these to your `~/.zshrc` or `~/.bashrc` to persist them across sessions.

## Usage

```bash
python claude_review.py --pr https://github.com/owner/repo/pull/123
```

Or if installed globally:

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

### Redirect output to a file

```bash
claude-review --pr https://github.com/owner/repo/pull/42 > review.md
```

### Example

```bash
$ claude-review --pr https://github.com/anthropics/anthropic-sdk-python/pull/756
Fetching PR anthropics/anthropic-sdk-python#756...
Sending diff to Claude for review...

# PR Review: [anthropics/anthropic-sdk-python#756](https://github.com/anthropics/anthropic-sdk-python/pull/756)

## Summary
...
```

## Output Format

The tool outputs structured Markdown with four sections:

| Section | Description |
|---|---|
| **Summary** | 2–3 sentence overview of what the PR does |
| **Identified Risks** | Bulleted list of potential bugs, security issues, or regressions |
| **Improvement Suggestions** | Bulleted list of actionable suggestions for the author |
| **Confidence Score** | `Low / Medium / High` with a brief rationale |

## Sample Outputs

See the [`sample_outputs/`](./sample_outputs/) directory for two real PR reviews:

- [`sample_outputs/review_anthropic_sdk.md`](./sample_outputs/review_anthropic_sdk.md) — review of a small bug fix PR
- [`sample_outputs/review_django_fix.md`](./sample_outputs/review_django_fix.md) — review of a feature addition PR

## Notes

- Large diffs are automatically truncated at ~80,000 characters to stay within Claude's context limits.
- Progress messages are written to stderr so stdout contains only the clean Markdown review.
- Uses `claude-opus-4-6` by default for the highest quality reviews.
