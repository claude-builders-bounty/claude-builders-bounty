# claude-review

`claude-review` fetches a GitHub pull-request diff, sends the untrusted diff to Claude Code in non-interactive mode, and prints a structured Markdown review.

## Requirements

- Python 3.10+
- Claude Code installed and authenticated
- Network access to GitHub
- Set `GITHUB_TOKEN` when reviewing private repositories or when authenticated API access is needed

The current Claude Code CLI supports non-interactive queries with `claude -p "query"`. This tool passes the PR payload over stdin so diff contents never become shell syntax.

## Install

From the repository root:

```bash
mkdir -p "$HOME/.local/bin" && cp claude-review/claude-review "$HOME/.local/bin/claude-review" && chmod +x "$HOME/.local/bin/claude-review"
```

Make sure `$HOME/.local/bin` is on `PATH`.

## Usage

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

For a private repository, export a GitHub token in `GITHUB_TOKEN` before running the same command.

Optional model selection:

```bash
claude-review --model sonnet --pr https://github.com/owner/repo/pull/123
```

## Output contract

The command prints exactly four review sections:

```markdown
## Summary
2-3 sentences.

## Risks
- Risk list.

## Improvement Suggestions
- Concrete suggestions.

## Confidence
Low | Medium | High
```

The CLI rejects a response that does not contain those sections in order or uses any other confidence value.

## Retrieval and trust boundary

The PR URL is parsed locally. Metadata and the unified diff are fetched from GitHub's pull-request REST endpoint. Private-repository access uses `GITHUB_TOKEN` if set. Diffs are capped at 500,000 characters by default; `--max-diff-chars` changes that ceiling.

PR titles, author names, metadata, and patch text are explicitly wrapped as untrusted review data. The Claude instruction says not to follow commands, prompts, tool requests, or role changes embedded in that content. The CLI invokes `claude` with an argument vector rather than `shell=True`.

## Real-PR sample outputs

Two required real-PR review outputs are included:

- `samples/cbb3-pr-4371.md` — https://github.com/claude-builders-bounty/claude-builders-bounty/pull/4371
- `samples/libpcap-pr-1752.md` — https://github.com/the-tcpdump-group/libpcap/pull/1752
