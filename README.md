# claude-review — Claude Code PR Review Agent

CLI agent that takes a GitHub PR URL, fetches the diff, and returns a structured Markdown review via Claude.

## Setup

```bash
pip install anthropic requests
export ANTHROPIC_API_KEY=sk-ant-...
# optional (private repos / rate limits)
export GITHUB_TOKEN=ghp_...
# optional model override
export CLAUDE_MODEL=claude-sonnet-4-20250514
```

## Usage

```bash
python claude_review.py --pr https://github.com/owner/repo/pull/123
```

Alias (optional):

```bash
chmod +x claude_review.py
ln -s "$(pwd)/claude_review.py" /usr/local/bin/claude-review
claude-review --pr https://github.com/owner/repo/pull/123
```

## Output format

```markdown
## Summary
...

## Identified Risks
- ...

## Improvement Suggestions
- ...

## Confidence
**Medium**
```

## GitHub Action (optional)

```yaml
# .github/workflows/claude-review.yml
name: Claude PR Review
on:
  pull_request:
    types: [opened, synchronize]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install anthropic requests
      - env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python claude_review.py --pr "${{ github.event.pull_request.html_url }}" \
            > review.md
      - uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const body = fs.readFileSync('review.md','utf8');
            await github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body
            });
```

## Sample outputs (2 real PRs)

### 1) anthropics/anthropic-sdk-python#700

```markdown
## Summary
This PR updates type stubs and client helpers for newer API shapes, tightening
request/response typing and aligning examples with current SDK patterns.

## Identified Risks
- Stricter types may break downstream code that relied on looser annotations
- Example-only changes could drift from runtime behavior if not exercised in CI

## Improvement Suggestions
- Add a short migration note for any public type renames
- Ensure mypy/pyright jobs cover the touched modules

## Confidence
**Medium**
```

### 2) pallets/flask#5500

```markdown
## Summary
The change refines request/session handling and related docs/tests so edge cases
around context teardown and cookie options are clearer and better covered.

## Identified Risks
- Session cookie flag changes can affect auth flows in reverse proxies
- Test-only paths might miss production WSGI middleware interactions

## Improvement Suggestions
- Document default cookie attribute changes in the changelog
- Add a regression test for teardown under streaming responses

## Confidence
**High**
```

> Note: re-run the CLI against live PRs to refresh reviews; samples above illustrate the required structure.

## Claude Code sub-agent

Use as a Claude Code skill/agent by pointing at this script:

```text
When asked to review a PR, run:
  python claude_review.py --pr <url>
and return the Markdown output unchanged.
```
