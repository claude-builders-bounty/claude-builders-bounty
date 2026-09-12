# claude-review CLI + GitHub Action

Issue #4 solution bundle for structured PR review output.

## 1) Install

```bash
chmod +x claude-review
```

## 2) Run

```bash
python3 claude-review --pr https://github.com/<owner>/<repo>/pull/<number>
python3 claude-review --pr ... --to-file review.md
```

## 3) Output format

- `### Summary`
- `### Risks`
- `### Suggestions`
- `### Confidence`

## 4) GitHub Action

A workflow is included at `.github/workflows/claude-review.yml` and runs on pull_request_target.

## 5) Validation evidence

Sample outputs are committed for real PRs:
- `sample-review-4225.md`
- `sample-review-4217.md`
