# claude-review — PR reviewer for Claude Code / GitHub Actions

Takes a GitHub PR URL, fetches its diff + title, and posts a structured Markdown review comment.

## Usage

```bash
# stdout
gh pr view https://github.com/owner/repo/pull/123 --json files --jq '.files[].path' > files.txt
node claude-review.cjs --pr https://github.com/owner/repo/pull/123
# post comment (needs GH_TOKEN)
node claude-review.cjs --pr https://github.com/owner/repo/pull/123 --post
```

Output sections: **Summary** (1–2 sentences + `additions/deletions/files`), **Risks**, **Suggestions**, **Confidence: Low / Medium / High**.

## GitHub Action

Create `.github/workflows/claude-review.yml`:

```yaml
name: Claude PR Review
on:
  pull_request:
    types: [opened, synchronize, reopened]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run claude-review
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        shell: bash
        run: |
          curl -fsSL https://raw.githubusercontent.com/breezesamuel/claude-builders-bounty/bounty-004-helium/bounty-004-pr-reviewer/claude-review.cjs -o /tmp/claude-review.cjs
          node /tmp/claude-review.cjs --pr "https://github.com/${{ github.repository }}/pull/${{ github.event.pull_request.number }}" --post
```

## Tested against real PRs

See `samples/5252.md` and `samples/5253.md` for raw output from live PRs.

## Known limits

- Heuristic bucket detection by file path, not by compiler. For deep semantic issues, pair with human review.
- Empty diff → Confidence = Low, a hint that there is nothing to merge.
