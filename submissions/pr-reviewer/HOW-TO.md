# How-To Guide: Claude Code PR Reviewer

## Prerequisites

```bash
pip install anthropic
export ANTHROPIC_API_KEY=sk-ant-your-key-here
```

You also need `gh` CLI installed and authenticated: `gh auth login`

---

## Basic Review

```bash
python claude-review.py https://github.com/facebook/react/pull/12345
```

This will:
1. Fetch the PR metadata (title, description, files changed)
2. Fetch the full diff
3. Send to Claude Sonnet for analysis
4. Print structured review to terminal

---

## Save Review to File

```bash
python claude-review.py https://github.com/owner/repo/pull/123 -o review.md
```

Useful for archiving reviews or sharing with the team.

---

## Post Review as PR Comment

```bash
python claude-review.py https://github.com/owner/repo/pull/123 --post
```

This posts the review directly as a comment on the PR. The author and other reviewers will see it immediately.

---

## Review Local Diff

For reviewing changes before pushing:

```bash
git diff main > changes.diff
python claude-review.py --diff changes.diff
```

---

## Use in CI/CD (GitHub Actions)

```yaml
# .github/workflows/pr-review.yml
name: AI PR Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install anthropic
      
      - name: Run AI Review
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python claude-review.py ${{ github.event.pull_request.html_url }} --post
```

This automatically reviews every PR when it's opened or updated.

---

## Understanding the Output

### Summary
A brief overview of what the PR does. Helps you quickly decide if this PR is what you expected.

### Risks
Things that could break in production:
- Security vulnerabilities (SQL injection, XSS, exposed secrets)
- Performance issues (N+1 queries, missing indexes)
- Logic bugs (off-by-one, race conditions)
- Breaking changes (API signature changes, removed exports)

### Suggestions
Actionable improvements with specific file and line references:
- "**file.py:42**: Consider using `with` statement for file handling"
- Better patterns, cleaner code, missing tests

### Confidence
How sure the reviewer is about its assessment:
- **High** — clear code, well-understood patterns, obvious issues
- **Medium** — some ambiguity, context-dependent suggestions
- **Low** — complex domain, insufficient context, unclear intent

---

## Tips

### For better reviews:
- Write descriptive PR titles and descriptions
- Keep PRs focused (one feature per PR)
- Include context about why, not just what

### Limitations:
- Diffs over 15k chars are truncated (very large PRs get partial review)
- Cannot run tests or build the project
- May miss context from files not in the diff
- Works best on application code (less useful for generated files, configs)
