# Claude Review Agent

A simple CLI tool that uses Claude to automatically review GitHub Pull Requests.

## Setup

1. Install dependencies:
   ```bash
   pip install requests anthropic
   ```
2. Set your Anthropic API key:
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-..."
   ```

## Usage

Run the script by providing the URL to a GitHub Pull Request:

```bash
python3 claude-review.py --pr https://github.com/owner/repo/pull/123
```

## How it works

1. It fetches the raw `.diff` for the given PR from GitHub.
2. It sends the diff to `claude-3-7-sonnet-20250219` with a strict prompt to categorize the review.
3. It prints a structured Markdown review directly to your terminal.
