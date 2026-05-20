# claude-review

A Claude Code sub-agent that reviews a GitHub pull request and produces a structured Markdown review with **Summary**, **Identified Risks**, **Improvement Suggestions**, and **Confidence score**.

## Quick Start

```bash
# 1. Install (single file, no dependencies beyond curl/jq/claude)
sudo cp claude-review /usr/local/bin/claude-review && sudo chmod +x /usr/local/bin/claude-review

# 2. (Optional) Customise the review prompt
cp review-prompt.txt ~/.config/claude-review/review-prompt.txt

# 3. Review a PR
claude-review --pr https://github.com/owner/repo/pull/123

# 4. Or review + post as a PR comment
claude-review --pr https://github.com/owner/repo/pull/123 --post
```

## Requirements

- **curl** — fetches PR diffs via GitHub API (pre-installed on macOS/Linux)
- **jq** — parses PR metadata (`brew install jq` / `apt install jq`)
- **claude** — Claude Code CLI (`npm install -g @anthropic-ai/claude-code`)
- **gh** (optional) — GitHub CLI for authenticated private repos and `--post` mode

## Output Structure

Every review follows the same structured format:

```markdown
## 🤖 Claude Code Review

> **PR:** [owner/repo#N](url) — title
> **Author:** @username
> **Stats:** +X / -Y, N file(s)

## Summary
2-3 sentences describing what the PR changes and why.

## Identified Risks
- Category — explanation
- ...

## Improvement Suggestions
- Actionable suggestion
- ...

## Confidence
High / Medium / Low — one-sentence justification.
```

## Sample Outputs

See the `sample-outputs/` directory for reviews generated from real PRs:

- [PR #1772 — safe-bash hook](sample-outputs/pr-1772-safe-bash.md) (+529 lines, 5 files)
- [PR #1768 — CLAUDE.md template](sample-outputs/pr-1768-claude-md.md) (+176 lines, 1 file)

Both were produced by running `claude-review --pr <url>` and pasting the output verbatim.

## Customising the Review Prompt

The review prompt lives at `review-prompt.txt` (sibling to the script). To override:

```bash
mkdir -p ~/.config/claude-review
cp review-prompt.txt ~/.config/claude-review/review-prompt.txt
# edit ~/.config/claude-review/review-prompt.txt
```

The script loads `$SCRIPT_DIR/review-prompt.txt` first, then falls back to a built-in default if the file is missing.

## How It Works

1. **Parse** — extracts `owner/repo/number` from the PR URL
2. **Fetch** — uses `gh pr diff` (if authenticated) or `curl` against the GitHub API (for public repos) to get the diff and metadata
3. **Truncate** — diffs over 64 KB are truncated to avoid token exhaustion
4. **Prompt** — builds a structured prompt with the diff + review template
5. **Review** — pipes the prompt to `claude --print --output-format markdown`
6. **Output** — wraps the review in a consistent `🤖 Claude Code Review` header with PR metadata
7. **Post** — optionally posts the review as a GitHub PR comment via `gh pr comment`

## Design Decisions

- **gh-first, curl-fallback.** Uses `gh` when authenticated (private repos, `--post` mode) and falls back to curl for public repo diffs — no API key required.
- **64 KB diff cap.** Large diffs are truncated to avoid exhausting Claude's context window. The truncation is noted in the output so the reviewer knows the review is partial.
- **No pip deps.** The script is pure bash. The prompt template is plain text. Zero install-time surprises.
- **Structured output, not unstructured prose.** Every review has the same four sections so the reader knows what they're getting.

## Uninstall

```bash
sudo rm /usr/local/bin/claude-review
rm -rf ~/.config/claude-review
```
