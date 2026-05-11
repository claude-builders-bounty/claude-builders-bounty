# Claude Code PR Review Agent

A lightweight Python script that analyzes GitHub PR diffs and returns structured Markdown reviews. Works as a CLI tool or a GitHub Action.

## Features

- **Structured output**: Summary of changes, risks, improvement suggestions, confidence score
- **Security scanning**: Detects hardcoded secrets, SQL injection vectors, XSS risks, eval(), debug code
- **Quality checks**: Line length violations, file size warnings, TODO/FIXME markers
- **Works standalone**: No database, no LLM API needed — pure static analysis

## Usage

### CLI

```bash
# By URL
python claude-review.py --pr https://github.com/owner/repo/pull/123

# By components
python claude-review.py --owner owner --repo repo --number 123

# With GitHub token (for private repos)
python claude-review.py --pr https://github.com/owner/repo/pull/123 --token ghp_xxx
```

### GitHub Action

Copy `.github/workflows/claude-review.yml` from this repo or use the `claude-review.yml` in this PR:

```yaml
name: PR Review Agent
on: [pull_request_target]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - name: Run review
        run: python claude-review.py --owner ${{ github.event.repository.owner.login }} --repo ${{ github.event.repository.name }} --number ${{ github.event.pull_request.number }} > review.md
      - name: Post comment
        uses: actions/github-script@v7
        with:
          script: const fs = require('fs'); github.rest.issues.createComment({ issue_number: context.issue.number, owner: context.repo.owner, repo: context.repo.repo, body: fs.readFileSync('review.md','utf8') });
```

## Sample Outputs

See [`SAMPLE_PR_977.md`](./SAMPLE_PR_977.md) — review of a 254-line PR with 4 files.
See [`SAMPLE_PR_994.md`](./SAMPLE_PR_994.md) — review of a 798-line PR with 7 files.

## How It Works

1. Fetches the PR diff from GitHub API
2. Parses added/removed lines per file
3. Scans for security patterns (secrets, SQLi, XSS, eval, debug code)
4. Checks code quality (line length, file size, incomplete work markers)
5. Generates structured Markdown with confidence score

## Confidence Scoring

| Scenario | Score |
|----------|-------|
| < 20 lines, simple change | High |
| 20-100 lines | Medium |
| 100+ lines or risks detected | Medium |
| 500+ lines or 3+ risks | Low |
