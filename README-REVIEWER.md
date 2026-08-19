# Claude PR Reviewer Agent

A lightweight, automated CLI tool that uses Anthropic's Claude to review GitHub Pull Requests. It automatically fetches the `.diff` of any public PR and returns a structured Markdown review containing summaries, risk assessments, and improvement suggestions.

## Setup

1. **Install Python 3.7+** (no external dependencies needed, uses standard library).
2. **Export your Anthropic API Key:**
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-..."
   ```

## Usage

Run the agent via the CLI and point it to any GitHub PR:

```bash
python3 claude-review.py --pr https://github.com/owner/repo/pull/123
```

## Example Output

```markdown
### Summary
This PR implements the new user authentication flow by adding a `/login` route and integrating JWT token generation. It also includes corresponding unit tests to verify login success and failure states.

### Identified Risks
- Hardcoded secret keys are used in `auth.py` which could be exposed if this code goes to production.
- No rate limiting is implemented on the `/login` endpoint, making it susceptible to brute-force attacks.

### Improvement Suggestions
- Move the JWT secret to an environment variable and load it via `os.environ`.
- Add a basic rate limiting middleware to prevent brute-forcing.

### Confidence Score
High
```
