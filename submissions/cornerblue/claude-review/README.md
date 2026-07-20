# claude-review — structured PR review agent ($150)

CLI + optional GitHub Action that produces a structured Markdown PR review.

## Output shape

- Summary of changes (2–3 sentences)
- Identified risks (list)
- Improvement suggestions (list)
- Confidence score: Low / Medium / High

## CLI

```bash
chmod +x claude-review
./claude-review --pr https://github.com/owner/repo/pull/123
# or
./claude-review --diff ./local.patch --out review.md
```

Requires `gh` auth for `--pr` mode.

## GitHub Action

Copy `.github/workflows/claude-review.yml` into a repo. On each PR it posts a structured review comment.

## Sample outputs

See `samples/` for reviews of real public PRs.

## Author

@cornerblue — BTC `bc1qjtevjy8gldfhkra6n5g4yclpr5uafyd7k0j2ls`
