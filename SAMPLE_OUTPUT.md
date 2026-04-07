# PR Review Sample Outputs

## Example 1: coollabsio/coolify PR #9436

```markdown
## 🔍 PR Review
**Confidence**: Medium

### Summary
PR modifies 4 file(s) with 47 deletions and 3 additions. Changes remove Algora bounty program references from docs/templates.

📊 **4** files · **3** additions · **47** deletions

### ⚠️ Risks
- No major risks detected

### 💡 Suggestions
- Found 1 TODO/FIXME comment(s)
- No version bump or changelog — document changes for release notes

— *Review by claude-review*
```

## Usage with GitHub Action

Add to `.github/workflows/pr-review.yml`:

```yaml
name: PR Review
on: [pull_request]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run PR Review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          pip install claude-review
          claude-review --pr ${{ github.event.pull_request.html_url }} --post
```
