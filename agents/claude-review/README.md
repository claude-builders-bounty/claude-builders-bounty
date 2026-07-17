# claude-review

CLI that turns a GitHub PR into a **structured Markdown review**:

- Summary (2–3 sentences)
- Identified risks
- Improvement suggestions
- Confidence: Low / Medium / High

Heuristic analysis (no paid LLM required). Works as a stand-alone agent script or in CI.

## Setup

```bash
# needs GitHub auth for private PRs / higher rate limits
gh auth login   # or export GITHUB_TOKEN=...
pip install -r requirements.txt   # none required; stdlib only
```

Optional install as command:

```bash
chmod +x claude_review.py
# alias or copy to PATH as claude-review
```

## Usage

```bash
python claude_review.py --pr https://github.com/owner/repo/pull/123
python claude_review.py --pr owner/repo#123 -o review.md
python claude_review.py --diff ./local.patch
```

GitHub Action: see `../../.github/workflows/claude-review.yml` (optional workflow in this package folder: `action.yml` pattern below).

### GitHub Action (drop-in)

```yaml
# .github/workflows/claude-review.yml
name: claude-review
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
          python-version: "3.12"
      - name: Review PR
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python agents/claude-review/claude_review.py \
            --pr "${{ github.repository }}#${{ github.event.pull_request.number }}" \
            -o /tmp/review.md
          cat /tmp/review.md >> $GITHUB_STEP_SUMMARY
```

## Sample outputs

See `samples/` for reviews of real public PRs.

## Tests

```bash
python -m unittest test_claude_review.py -v
```
