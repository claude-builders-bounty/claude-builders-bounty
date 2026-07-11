# claude-review — structured PR review agent

**Bounty:** #4 — $150 (Opire)

## Setup

```bash
# needs: python3, gh (authenticated)
pip install --quiet  # no third-party deps required
```

Optional: set `ANTHROPIC_API_KEY` for model-backed reviews (falls back to heuristics).

## Usage

```bash
# CLI (as required by bounty)
python claude_review.py --pr https://github.com/owner/repo/pull/123

# or install wrapper
chmod +x claude-review
./claude-review --pr https://github.com/owner/repo/pull/123

# local diff
python claude_review.py --diff ./change.diff --json
```

## Output sections

1. Summary of changes (2–3 sentences)  
2. Identified risks  
3. Improvement suggestions  
4. Confidence: Low / Medium / High  

## GitHub Action

Copy `../.github/workflows` path: use workflow file  
`bounties/04-pr-review-agent/.github/workflows/claude-review.yml`  
into your repo’s `.github/workflows/`.

## Samples (real PRs)

- `samples/review-pr-3363.md` — claude-builders-bounty#3363  
- `samples/review-pr-3364.md` — claude-builders-bounty#3364  
