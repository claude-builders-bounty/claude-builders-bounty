# PR review

Builds a structured Markdown review from a real GitHub pull request diff. It uses the GitHub CLI. It does not call a model API and it does not post the comment.

## Setup

```
gh auth status
python3 claude_review.py --pr https://github.com/owner/repo/pull/123
```

## Output

The command prints four sections: Summary, Risks, Suggestions, and Confidence. Confidence is High when no risk pattern matched and the added diff is at most 200 lines, Medium when one risk matched or the diff is larger, and Low when two risks matched or more than 800 lines were added.

## Samples

sample-flask-5914.md and sample-click-3865.md are outputs from two merged public pull requests. They are checked into this folder so a reviewer can read them without rerunning the command.
