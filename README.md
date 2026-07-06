# Claude Review Agent

A CLI tool that uses Claude to review GitHub pull requests.

## Setup

1. Clone this repository.
2. Install dependencies:
   ```bash
   pip install requests
   ```
3. Set environment variables:
   ```bash
   export CLAUDE_API_KEY="your-anthropic-api-key"
   export GITHUB_TOKEN="your-github-token"  # optional, needed to post comments and fetch private repos
   ```

## Usage

### Basic review (output to console)
```bash
python claude_review.py --pr https://github.com/owner/repo/pull/123
```

### Save review to file
```bash
python claude_review.py --pr https://github.com/owner/repo/pull/123 --output review.md
```

### Post review as a comment on the PR
```bash
python claude_review.py --pr https://github.com/owner/repo/pull/123 --post
```

## GitHub Action

You can also use the included workflow. Create `.github/workflows/pr-review.yml` in your repository with the following content:

```yaml
name: PR Review using Claude
on:
  pull_request:
    types: [opened, synchronize]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install requests
      - name: Run Claude review
        env:
          CLAUDE_API_KEY: ${{ secrets.CLAUDE_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python claude_review.py --pr "${{ github.event.pull_request.html_url }}" --post
```

Make sure to add `CLAUDE_API_KEY` and `GITHUB_TOKEN` as secrets in your repository settings.

## Output Format

The review is a Markdown document with the following sections:
- **Summary**: 2-3 sentences describing the changes.
- **Identified Risks**: Bullet list of potential issues.
- **Improvement Suggestions**: Bullet list of suggestions.
- **Confidence Score**: Low / Medium / High.

## Sample Outputs

### Sample 1: Add user authentication
[Link to PR](https://github.com/example/demo/pull/1)

```markdown
**Summary**: This PR adds JWT-based authentication to the API. It includes login and token refresh endpoints, middleware for protecting routes, and database schema for storing tokens. The changes are well-structured but lack error handling for expired tokens.

**Identified Risks**:
- No token blacklist mechanism for logout
- Hardcoded secret key in source code
- No rate limiting on login endpoint

**Improvement Suggestions**:
- Move secret key to environment variable
- Add token expiration and refresh flow
- Implement rate limiting to prevent brute force

**Confidence Score**: Medium
```

### Sample 2: Refactor database queries
[Link to PR](https://github.com/example/demo/pull/2)

```markdown
**Summary**: This PR refactors database query functions to use a centralized query builder. It reduces code duplication but introduces a new dependency. The changes are mostly safe but require thorough testing.

**Identified Risks**:
- New dependency without version pinning
- Potential breaking changes in edge cases
- Missing migration for existing queries

**Improvement Suggestions**:
- Pin dependency version
- Add unit tests for all refactored functions
- Document migration steps

**Confidence Score**: High
```

## License
MIT
