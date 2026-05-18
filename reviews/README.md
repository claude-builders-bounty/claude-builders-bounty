# 🤖 claude-review — AI PR Reviewer Agent

[Bounty #4 — $150](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4)

A Claude Code sub-agent that reviews GitHub PRs and posts structured Markdown comments.

## ✨ Features

- **CLI mode**: `claude-review --pr https://github.com/owner/repo/pull/123`
- **GitHub Action mode**: Auto-comment on PRs (workflow YAML included)
- **Structured output**: Summary, risks, suggestions, confidence score
- **Risk detection**: Hardcoded secrets, SQL injection risks, console.log, TODOs, large diffs
- **JSON output**: Machine-parseable for CI integration

## 🚀 Quick Start

### CLI

```bash
# Install
pip install -r requirements.txt

# Review any PR
python claude_review.py --pr https://github.com/owner/repo/pull/123

# JSON output
python claude_review.py --pr https://github.com/owner/repo/pull/123 --json

# Save to file
python claude_review.py --pr https://github.com/owner/repo/pull/123 --output review.md
```

### GitHub Action

Add `.github/workflows/pr-review.yml` to any repo:

```yaml
name: PR Review
on: [pull_request]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: |
          pip install requests
          python claude_review.py --pr "${{ github.event.pull_request.html_url }}" --output review.md
      - uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const body = fs.readFileSync('review.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: body
            });
```

## 📋 Output Format

```markdown
## 🔍 PR Review

### 📊 Diff Stats
- **3** files changed
- **120+** additions
- **15-** deletions

### 📋 Summary
This PR modifies **3 files** with **120+** and **15-** lines of changes.

### ⚠️ Identified Risks
- Possible hardcoded secret detected
- Large diff detected — review thoroughly

### 💡 Improvement Suggestions
- Consider splitting this PR into smaller changes
- Ensure all new code has corresponding unit tests

### 🎯 Confidence Score: **Medium**
```

## 🧪 Tested On

| PR | Result |
|:---|:-------|
| [#1516](https://github.com/claude-builders-bounty/claude-builders-bounty/pull/1516) — CLAUDE.md template | ✅ High confidence, clean analysis |
| [#1508](https://github.com/claude-builders-bounty/claude-builders-bounty/pull/1508) — Changelog generator | ✅ High confidence, clean analysis |

See [SAMPLE_OUTPUTS.md](./SAMPLE_OUTPUTS.md) for full output.

## ✅ Acceptance Criteria

| Criteria | Status |
|:---------|:------:|
| CLI mode: `claude-review --pr <url>` | ✅ |
| GitHub Action YAML included | ✅ |
| Structured Markdown: summary + risks + suggestions + confidence | ✅ |
| Tested on 2 real PRs | ✅ |
| README with setup and usage | ✅ |
