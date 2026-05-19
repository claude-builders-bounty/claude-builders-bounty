# Claude Code PR Review Agent

A CLI sub-agent that automatically fetches the diff of a GitHub PR, analyzes the code changes using the Claude API, and outputs a structured Markdown code review.

## Features
- Connects directly to GitHub to fetch the raw diff of any public PR (or private, if `GITHUB_TOKEN` is set).
- Passes the diff context to Claude via Anthropic's Messages API.
- Generates a structured Markdown review including:
  - Summary of changes
  - Identified risks
  - Improvement suggestions
  - Confidence score

## Setup

1. Install required dependencies:
   ```bash
   pip install requests
   ```

2. Set your Anthropic API Key (and optionally your GitHub token to avoid rate limits):
   ```bash
   export ANTHROPIC_API_KEY="your-api-key"
   export GITHUB_TOKEN="your-github-token" # optional
   ```

3. Make the script executable:
   ```bash
   chmod +x claude-review.py
   ```

## Usage

Run the agent via CLI by passing the GitHub PR URL:

```bash
./claude-review.py --pr https://github.com/owner/repo/pull/123
```

## Sample Output

```md
### Summary of changes
This PR implements a new logging middleware for the express application, replacing the old console.log statements. It also updates the error handling logic to gracefully catch database connection timeouts.

### Identified risks
- The new logger instance is created synchronously on every request, which might introduce performance overhead.
- The timeout error catch block assumes the error object has a `.code` property without checking if it's undefined, which could cause a fatal crash.

### Improvement suggestions
- Instantiate the logger once at module level and reuse it across requests.
- Add optional chaining or explicit type checking when handling the database error in `app.js` (line 42).

### Confidence score
High
```
