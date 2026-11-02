# claude-review

A Claude Code based PR reviewer. Give it a GitHub PR URL; it fetches the diff, asks Claude to review it, and prints (or posts) a structured Markdown comment:

- **Summary** (2-3 sentences)
- **Risks** (list)
- **Suggestions** (list)
- **Confidence** (Low / Medium / High)

## Requirements
- Python 3.8+ (standard library only)
- Either [Claude Code](https://claude.com/claude-code) (`claude` on `PATH`, authenticated) or `ANTHROPIC_API_KEY` set
- `GITHUB_TOKEN` (optional for public PRs, needed for private repos, higher rate limits and `--post`)

## Setup
```bash
chmod +x pr-reviewer/claude-review
sudo ln -s "$PWD/pr-reviewer/claude-review" /usr/local/bin/claude-review
export ANTHROPIC_API_KEY=...   # not needed if `claude` is already logged in
```

## Usage
```bash
claude-review --pr https://github.com/owner/repo/pull/123            # print review
claude-review --pr https://github.com/owner/repo/pull/123 --post     # also comment on the PR
claude-review --pr ... --output review.md                            # also save to file
claude-review --pr ... --dry-run                                     # show the prompt only
```
Set `CLAUDE_REVIEW_MODEL` to change the model used by the API fallback. `CLAUDE_REVIEW_MOCK=<file>` replaces the model call (tests only).

Diffs over 120k characters are truncated at a file boundary. The prompt treats all PR content as untrusted data. The tool exits non-zero with a clear message when no key is available or the model output lacks a required section.

A Claude Code sub-agent definition is in `agents/pr-reviewer.md` (copy it to `.claude/agents/` to use it); the shared rubric is `prompt.md`.

## GitHub Action
Copy `action/claude-review.yml` to `.github/workflows/claude-review.yml` and add an `ANTHROPIC_API_KEY` repository secret. It reviews each opened/updated PR (not PRs from forks, which cannot read secrets).

## Tests
```bash
python3 -m unittest discover -s pr-reviewer/tests -v
```

## Samples
See `samples/README.md`.
