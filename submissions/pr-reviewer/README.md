# AGENT: Claude Code PR Reviewer

> Bounty #4 — $150 | [Issue Link](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4)

## Setup (3 steps)

```bash
# 1. Install dependency
pip install anthropic

# 2. Set API key
export ANTHROPIC_API_KEY=sk-ant-your-key-here

# 3. Run
python claude-review.py https://github.com/owner/repo/pull/123
```

## Usage

```bash
# Review a PR by URL
python claude-review.py https://github.com/owner/repo/pull/123

# Review by owner/repo + number
python claude-review.py owner/repo 123

# Review a local diff file
python claude-review.py --diff changes.diff

# Save review to file
python claude-review.py https://github.com/owner/repo/pull/123 -o review.md

# Post review as PR comment directly
python claude-review.py https://github.com/owner/repo/pull/123 --post
```

## Output format

Every review follows this structured Markdown format:

```markdown
## Summary
[2-3 sentences on what the PR does and overall quality]

## Risks
- [Identified risk 1 with specific file:line reference]
- [Identified risk 2]

## Suggestions
- [Suggestion 1 with file:line and code context]
- [Suggestion 2]

## Confidence
**High/Medium/Low** — [Brief justification]
```

## Sample reviews

See the `sample-output-*.md` files for real reviews generated on actual PRs:

- **sample-output-1.md** — Review of a bash changelog generator (4 files, +459 lines)
- **sample-output-2.md** — Review of a safety hook Python script (3 files, +538 lines)

## Bonus features

- **`--post` flag** — posts review directly as a PR comment on GitHub
- **`--diff` mode** — review local diff files without GitHub
- **`--output` flag** — save to file for archival
- **Diff truncation** — handles large PRs by truncating to 15k chars
- **File list breakdown** — shows per-file additions/deletions in context
- **Specific line references** — suggestions reference exact file:line from the diff
- Uses `gh` CLI for authenticated GitHub access (private repos work too)

## Files

| File | Purpose |
|------|---------|
| `claude-review.py` | The reviewer script |
| `README.md` | This file |
| `HOW-TO.md` | Detailed guide |
| `sample-output-1.md` | Sample review of changelog skill PR |
| `sample-output-2.md` | Sample review of safety hook PR |
