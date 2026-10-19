# claude-review

CLI that produces a structured Markdown review for a GitHub PR.

## Setup (3 steps)
1. Install GitHub CLI (`gh`) and authenticate: `gh auth login`.
2. `pip install -r requirements.txt` (none required beyond stdlib).
3. Run: `python claude_review.py --pr https://github.com/owner/repo/pull/123`

## Usage
```
python claude_review.py --pr https://github.com/owner/repo/pull/123
python claude_review.py --pr https://github.com/owner/repo/pull/123 --post
```
