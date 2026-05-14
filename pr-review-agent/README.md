# Claude PR Review Agent 🤖

> **Bounty #4 — $150** — A Claude Code sub-agent that reviews GitHub PRs and posts structured Markdown comments.

## Features

- **CLI mode**: Review any public or private PR — `claude-review --pr <url>`
- **Local diff mode**: Review a patch file offline — `claude-review --diff patch.txt`
- **GitHub Action**: Auto-review every PR in your repo
- **Structured output**: Summary → Risks → Suggestions → Positives → Confidence
- **Static analysis**: 20+ security/quality patterns, commit message quality check, file impact analysis
- **Confidence scoring**: Low / Medium / High based on findings severity

## Quick Start

```bash
# Review a public PR
python claude-review.py --pr https://github.com/psf/black/pull/5129

# Review a local diff
python claude-review.py --diff path/to/patch.diff

# Save output to file
python claude-review.py --pr https://github.com/owner/repo/pull/123 -o review.md

# Use a GitHub token (for private repos or higher rate limit)
python claude-review.py --pr https://github.com/owner/repo/pull/123 --token ghp_xxxx
```

## Output Format

The review is a structured Markdown document with these sections:

| Section | Description |
|---------|-------------|
| **Summary** | 2-3 sentence overview + change statistics table |
| **Identified Risks** | Security vulnerabilities, dangerous patterns, hardcoded secrets |
| **Improvement Suggestions** | Code quality, style, architecture, test coverage |
| **What's Done Well** | Positive observations, clean patterns |
| **Review Confidence** | Low / Medium / High with recommendation |

## GitHub Action

Add this workflow to `.github/workflows/claude-review.yml`:

```yaml
name: Claude PR Review
on:
  pull_request:
    types: [opened, synchronize]

permissions:
  pull-requests: write
  contents: read

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Download claude-review agent
        run: |
          curl -sSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/pr-review-agent/claude-review.py \
            -o /tmp/claude-review.py
          chmod +x /tmp/claude-review.py

      - name: Run review
        id: review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          PR_URL="https://github.com/${{ github.repository }}/pull/${{ github.event.pull_request.number }}"
          /tmp/claude-review.py --pr "$PR_URL" --output /tmp/review.md

      - name: Post review comment
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const review = fs.readFileSync('/tmp/review.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: review
            });
```

## Analysis Capabilities

### Security (15 patterns)
- Hardcoded passwords, API keys, tokens
- SQL injection, XSS, unsafe deserialization
- Command injection (exec/eval/os.system)
- Weak crypto (MD5, SHA1)
- Privilege escalation (sudo, chmod 777)
- Debug code left in (breakpoint, pdb)

### Quality (10 patterns)
- Long lines, missing indentation
- Broad exception handling
- Magic numbers, hardcoded values
- TypeScript `any` / `@ts-ignore`
- Unimplemented stubs (TODO, NotImplementedError)

### Commit Quality
- WIP/unclear message detection
- Meaningful commit message recognition

### File Impact
- Large file change warnings
- Missing test file detection
- Lock file size checks
- Configuration file change tracking

## Sample Output

See [`examples/sample-pr-1.md`](examples/sample-pr-1.md) and [`examples/sample-pr-2.md`](examples/sample-pr-2.md) for full review examples.

## Requirements

- Python 3.8+
- `GITHUB_TOKEN` env var or `--token` flag (for private repos / higher rate limit)

## Installation

```bash
# Clone and use directly
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
cd pr-review-agent
chmod +x claude-review.py

# Or download standalone
curl -sSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/pr-review-agent/claude-review.py \
  -o /usr/local/bin/claude-review
chmod +x /usr/local/bin/claude-review
```

## Testing

```bash
# Run on a sample diff
python claude-review.py --pr https://github.com/psf/black/pull/5129
python claude-review.py --pr https://github.com/django/django/pull/21284
```
