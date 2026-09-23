# Claude PR review agent

`agents/claude-review.py` reviews a GitHub pull request diff and prints a structured Markdown review comment.

Usage:

```bash
python agents/claude-review.py --pr https://github.com/owner/repo/pull/123
```

Output includes:

- 2-sentence summary of touched files and line counts
- identified risks
- improvement suggestions
- confidence score: Low, Medium, or High

The agent uses deterministic diff heuristics and does not post comments automatically. It flags common risks such as destructive shell commands, unsafe SQL operations, possible secret assignments, network calls without obvious timeout review, and large diffs.

Run tests:

```bash
python -m unittest tests/test_claude_review.py
```
