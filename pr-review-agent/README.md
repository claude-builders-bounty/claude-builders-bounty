# Claude Code PR Review Agent

A CLI tool that analyzes GitHub PR diffs and produces structured Markdown reviews with risk assessment, improvement suggestions, and confidence scoring.

## Features

- **Risk Detection** — 10+ pattern categories: SQL injection, code injection, XSS, hardcoded secrets, path traversal, weak crypto, debug code, technical debt, error handling, supply chain
- **Structured Output** — Summary, risks (with severity), suggestions, confidence score
- **Multiple Input Modes** — PR URL, PR number + repo, or local `.diff` file
- **GitHub Action Support** — Works as a CI/CD step with auto-commenting
- **Zero External Dependencies** — Pure Python 3.8+, only requires `gh` CLI for fetching PRs

## Installation

```bash
# Clone or download claude_review.py
chmod +x claude_review.py

# Optional: add to PATH
sudo ln -s $(pwd)/claude_review.py /usr/local/bin/claude-review
```

### Requirements

- Python 3.8+
- [gh CLI](https://cli.github.com/) (authenticated) — for `--pr` mode

## Usage

### Review a PR by URL

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

### Review a PR by number

```bash
claude-review --pr 123 --repo owner/repo
```

### Analyze a local diff file

```bash
claude-review --diff changes.diff
```

### Save to file

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

### JSON output (for scripting)

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --json
```

## Output Format

The review includes:

1. **Summary** — 2-3 sentence overview of changes, languages, and overall confidence
2. **Identified Risks** — Categorized list with severity (🔴 Critical / 🟠 High / 🟡 Medium / 🔵 Low) and code snippets
3. **Improvement Suggestions** — Actionable recommendations based on analysis patterns
4. **Confidence Score** — High / Medium / Low with rationale

## Risk Categories

| Category | Severity | Patterns Detected |
|----------|----------|-------------------|
| Destructive SQL | Critical | DROP TABLE, TRUNCATE, DELETE FROM without WHERE |
| Code Injection | Critical | eval(), exec(), os.system, shell=True |
| Security | High | Hardcoded passwords/secrets/API keys |
| Path Traversal | High | rm -rf, ../ paths |
| XSS | High | innerHTML, dangerouslySetInnerHTML |
| Cryptography | Critical | Weak random/token generation |
| Debug Code | Low | console.log, print() statements |
| Technical Debt | Medium | TODO/FIXME/HACK markers |
| Error Handling | Medium | Bare except clauses |
| Supply Chain | Medium | npm install without audit |

## GitHub Action

See [`claude-review.yml`](./claude-review.yml) for the workflow definition.

Add to your repo's `.github/workflows/` directory:

```yaml
name: PR Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
      contents: read
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r pr-review-agent/requirements.txt
      - name: Run PR Review
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python pr-review-agent/claude_review.py \
            --pr ${{ github.event.pull_request.number }} \
            --repo ${{ github.repository }} \
            --output /tmp/review.md
      - name: Post Review Comment
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const review = fs.readFileSync('/tmp/review.md', 'utf8');
            github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body: review
            });
```

## How It Works

1. Fetches PR diff via `gh pr diff` (or reads from file)
2. Parses added lines, removed lines, and changed files
3. Runs pattern matching against 10+ risk rule categories
4. Generates contextual suggestions based on language, scope, and findings
5. Calculates confidence score from risk density and change size
6. Outputs structured Markdown (or JSON)

## Testing

The tool has been tested on real GitHub PRs. See [`test_outputs/`](./test_outputs/) for sample outputs.

Run a quick self-test:

```bash
# Test with a sample diff
echo 'diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -1,3 +1,4 @@
 import os
 def handle(req):
-    return "ok"
+    password = "admin123"
+    os.system(eval(req))
+    return process(req)' > /tmp/test.diff

python claude_review.py --diff /tmp/test.diff
```

## License

MIT
