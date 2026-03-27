# claude-review

A small CLI that reviews a GitHub pull request URL and produces a structured Markdown review.

## Usage

```bash
npm install
npm link
claude-review --pr https://github.com/OWNER/REPO/pull/123
```

## Output format

- Summary
- Risks
- Improvement Suggestions
- Confidence (Low / Medium / High)

## Notes

- Requires GitHub CLI (`gh`) to be installed and authenticated.
- Reads PR metadata and diff from GitHub, then applies a lightweight heuristic review.
- Sample outputs are in `examples/`.


## Development

```bash
npm test
./tests/integration-smoke.sh
```
