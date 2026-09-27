# PR review agent

This bounty submission provides both:

- a CLI: `python claude_review.py --pr <github-pr-url>`
- a GitHub Action that posts the generated Markdown review back to the pull request

The review output always contains:

- a 2-3 sentence-style summary of the change surface
- identified risks
- improvement suggestions
- a Low / Medium / High confidence label

## Usage

```bash
python claude_review.py --pr https://github.com/owner/repo/pull/123
```

The CLI retrieves the real pull-request diff with GitHub CLI (`gh pr diff`) and returns structured Markdown.

## Real PR verification

The agent was exercised against two real GitHub pull requests and the resulting outputs are committed with this submission:

1. https://github.com/claude-builders-bounty/claude-builders-bounty/pull/4375
   - output: `bounty-4/sample-output-1.md`
2. https://github.com/claude-builders-bounty/claude-builders-bounty/pull/4378
   - output: `bounty-4/sample-output-2.md`

## Automated verification

```bash
python -m unittest discover -s tests -p "test_*.py"
```

A GitHub Action workflow is included for automatic PR comments.
