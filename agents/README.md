# claude-review

Structured Markdown PR reviews from the command line.

## Setup

```bash
pip install -r requirements.txt  # none required — stdlib only
```

## Usage

```bash
python claude_review.py --pr https://github.com/owner/repo/pull/123
```

## Output

- Summary (2–3 sentences)
- Risks (bullet list)
- Suggestions (bullet list)
- Confidence: Low / Medium / High

## GitHub Action

See `.github/workflows/pr-review.yml`.
