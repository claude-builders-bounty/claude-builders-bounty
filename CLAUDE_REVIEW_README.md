# Claude Review Agent

AI-powered PR review agent for GitHub pull requests.

## Setup
```bash
export GITHUB_TOKEN=ghp_xxx
python3 claude_review.py --pr https://github.com/owner/repo/pull/123
```

## Usage
- `python3 claude_review.py --pr <url>` — Review via PR URL
- `python3 claude_review.py --pr owner/repo/123` — Review via short form
- `python3 claude_review.py --pr <url> --output review.md` — Save to file

## Output
Structured Markdown with Summary, Risks, Improvements, Confidence Score.

## Samples
See `review_sample_1.md` and `review_sample_2.md`.
