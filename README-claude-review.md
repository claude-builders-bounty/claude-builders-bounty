# Claude Review PR Agent

`claude-review` is a zero-dependency CLI that takes a GitHub pull request URL,
fetches the PR metadata and diff, and prints a structured Markdown review
comment.

It is designed as a lightweight Claude Code review sub-agent entry point: the
output is deterministic Markdown that Claude or a human maintainer can paste
into a PR conversation.

## Setup

```bash
chmod +x claude-review
```

Optional for higher GitHub API rate limits:

```bash
export GITHUB_TOKEN=ghp_...
```

## Usage

```bash
./claude-review --pr https://github.com/owner/repo/pull/123
```

## Output format

The review includes:

- Summary of changes in 2–3 sentences
- Identified risks
- Improvement suggestions
- Confidence score: Low / Medium / High

## What it checks

The heuristic scanner highlights common review risks:

- file deletion
- database/schema changes
- auth, token, secret, permission, and security-sensitive code
- network/API behavior
- shell/process execution
- dependency/config changes
- missing obvious test updates
- large diffs

## Sample outputs

Two real PR sample outputs are included in:

- `samples/review-claude-builders-2015.md`
- `samples/review-daydreams-198.md`

## Validation

```bash
python3 -m unittest discover -s tests -v
./claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2015
```
