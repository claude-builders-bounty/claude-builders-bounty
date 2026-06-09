# Claude Review CLI

Generate a structured Markdown review comment from a GitHub pull request diff.

## Setup

```bash
chmod +x claude-review
```

## Usage

```bash
./claude-review --pr https://github.com/owner/repo/pull/123
```

If you already use the GitHub CLI and want authenticated diff fetching:

```bash
./claude-review --pr https://github.com/owner/repo/pull/123 --use-gh
```

## Output

The CLI prints Markdown with:

- summary of changes,
- identified risks,
- improvement suggestions,
- confidence score: Low, Medium, or High.

## Tested Pull Requests

Sample outputs are included in:

- `samples/claude-builders-2635.md`
- `samples/turso-7414.md`

## Local Verification

```bash
python3 test_claude_review.py
python3 -m py_compile claude_review.py test_claude_review.py
```
