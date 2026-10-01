# PR Review Sub-Agent

A CLI tool and GitHub Action to automatically review GitHub Pull Requests. It uses pattern matching to identify potential security issues, bugs, and performance bottlenecks, returning a structured Markdown review.

## Setup

1. Make sure you have the [GitHub CLI (`gh`)](https://cli.github.com/) installed and authenticated.
2. Clone this repository.
3. No additional Python dependencies are required.

## Usage

Run the CLI tool by passing a GitHub Pull Request URL:

```bash
python claude-review --pr https://github.com/owner/repo/pull/123
```

### Output format

The tool outputs a structured Markdown review containing:
- **Summary of Changes**: A brief overview of the lines modified.
- **Identified Risks**: Critical security vulnerabilities (like `eval()`, hardcoded secrets).
- **Improvement Suggestions**: Style and bug patterns (like bare `except:` blocks).
- **Confidence Score**: Low / Medium / High, based on the severity of identified issues.

## GitHub Action

You can integrate this tool directly into your CI/CD pipeline using the included GitHub Action. See `.github/workflows/pr-review.yml`.
