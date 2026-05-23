# claude-review-multimodel

A multi-backend CLI tool that reviews GitHub pull requests and outputs structured Markdown review comments. Works with three backends — **Claude CLI**, **Anthropic API**, and a zero-dependency **heuristic** fallback — so you can always get a review, even without any LLM API key.

## Features

- **Multi-backend**: `auto` mode picks the best available backend (`claude-cli` → `anthropic` → `heuristic`)
- **Heuristic fallback**: pure Python pattern analysis, zero dependencies, always works
- **Anthropic backend**: deep semantic review via Claude models
- **Claude CLI backend**: use your local `claude` binary for reviews
- **GitHub Action workflow**: automated PR reviews on open/sync or `/review` comment
- **Claude Code sub-agent**: `.claude/agents/pr-reviewer.md` for use inside Claude Code
- **Multiple input formats**: PR URL, `owner/repo#123`, or local diff file
- **Post comment**: `--post-comment` writes the review back to the PR
- **Diff truncation**: handles large diffs with automatic truncation and file summaries
- **Structured Markdown output**: Summary, Risks (severity table), Suggestions, Confidence score

## Quick Start

```bash
# Heuristic review (no API key needed)
python3 agents/claude-review-multimodel/claude_review.py \
  --pr https://github.com/expressjs/express/pull/6190 \
  --backend heuristic

# Or using the bash wrapper
agents/claude-review-multimodel/claude-review \
  --pr expressjs/express#6190 \
  --backend heuristic

# Anthropic backend (deep semantic review)
export ANTHROPIC_API_KEY="sk-ant-..."
python3 agents/claude-review-multimodel/claude_review.py \
  --pr https://github.com/owner/repo/pull/123 \
  --backend anthropic \
  --model claude-sonnet-4-20250514

# Claude CLI backend
python3 agents/claude-review-multimodel/claude_review.py \
  --pr https://github.com/owner/repo/pull/123 \
  --backend claude-cli

# Auto-select best available backend
python3 agents/claude-review-multimodel/claude_review.py \
  --pr https://github.com/owner/repo/pull/123 \
  --backend auto

# Save to file
python3 agents/claude-review-multimodel/claude_review.py \
  --pr https://github.com/owner/repo/pull/123 \
  --output review.md

# Post as PR comment (requires GITHUB_TOKEN)
export GITHUB_TOKEN="ghp_..."
python3 agents/claude-review-multimodel/claude_review.py \
  --pr https://github.com/owner/repo/pull/123 \
  --post-comment

# Review a local diff file
python3 agents/claude-review-multimodel/claude_review.py \
  --diff changes.diff \
  --backend heuristic
```

## CLI Options

| Option | Description |
|--------|-------------|
| `--pr URL_OR_REF` | GitHub PR URL or `owner/repo#123` |
| `--diff FILE` | Local diff file to review |
| `--backend auto|claude-cli|anthropic|heuristic` | Backend to use (default: auto) |
| `--model MODEL` | Model name for LLM backends |
| `--post-comment` | Post review as PR comment (needs GITHUB_TOKEN) |
| `--output FILE` | Write review to file instead of stdout |
| `--max-diff-bytes N` | Max diff size before truncation (default: 500000) |
| `--verbose` | Print progress to stderr |
| `--version` | Show version |

## Backend Details

### heuristic (always works)

Pure Python regex-based analysis. Detects:
- Hardcoded secrets/credentials (API keys, tokens, passwords)
- Debug statements (`print`, `console.log`, `debugger`, `pdb`)
- Empty catch blocks / bare `except: pass`
- TODO/FIXME/HACK comments
- Large file changes (>500 lines)
- Missing error handling patterns (resource leaks, unchecked HTTP responses)

Confidence is labeled honestly: heuristic reviews get **Low** confidence when no patterns are found (because they can't detect logic errors), and **Medium/High** when specific patterns match.

### anthropic (deep semantic review)

Calls the Anthropic Messages API with the full diff and a structured review prompt. Produces genuinely insightful reviews covering logic errors, architectural concerns, security vulnerabilities beyond pattern matching, and domain-specific issues.

Requires `ANTHROPIC_API_KEY` environment variable.

### claude-cli (local Claude binary)

Uses your locally installed `claude` CLI binary. Same semantic depth as the Anthropic backend, but runs through your local Claude Code installation. No API key needed if Claude Code is already configured.

### auto (default)

Tries backends in order: `claude-cli` → `anthropic` → `heuristic`. Picks the first one that's available (Claude CLI installed / Anthropic key set / always available).

## Output Format

Every review follows this structure:

```markdown
# PR Review: [Title]

**PR:** [URL]
**Author:** [author]
**Files Changed:** [N] | **Insertions:** +[N] | **Deletions:** -[N]
**Backend:** [backend] | **Model:** [model]

---

## Summary
[2-3 sentence overview]

## Identified Risks
| # | Severity | Category | Description | File(s) |
|---|----------|----------|-------------|---------|

## Improvement Suggestions
1. **[Category]** [Description] — `file:Lline`

## Confidence
**Score:** Low / Medium / High
**Rationale:** [Why this confidence level]
```

## GitHub Action

See `github-action/claude-review.yml` for a complete workflow that:
- Runs automatically on PR open / synchronize
- Runs on `/review` comment in PRs
- Posts the review as a PR comment
- Supports both heuristic and Anthropic backends

Setup:
1. Copy `github-action/claude-review.yml` to your repo's `.github/workflows/`
2. Add `ANTHROPIC_API_KEY` as a repository secret (optional — heuristic works without it)
3. `GITHUB_TOKEN` is automatically provided by GitHub Actions

## Claude Code Sub-Agent

`.claude/agents/pr-reviewer.md` defines a Claude Code sub-agent that can be invoked from within Claude Code sessions. When Claude Code sees a PR URL, it can delegate to this agent for structured review.

## Example Outputs

See `examples/` directory:
- `express-6190-heuristic.md` — Review of expressjs/express#6190 (small refactor PR, heuristic backend)
- `bottube-1175-heuristic.md` — Review of Scottcjn/bottube#1175 (feature PR, heuristic backend)

## Requirements

- Python 3.9+ (stdlib only, no external dependencies)
- Optional: `claude` CLI binary (for claude-cli backend)
- Optional: `ANTHROPIC_API_KEY` (for anthropic backend)
- Optional: `GITHUB_TOKEN` (for --post-comment and private repo access)

## Testing

```bash
# Syntax check
python3 -m py_compile agents/claude-review-multimodel/claude_review.py

# Heuristic review on a real PR
python3 agents/claude-review-multimodel/claude_review.py \
  --pr https://github.com/expressjs/express/pull/6190 \
  --backend heuristic --verbose

# Local diff review
python3 agents/claude-review-multimodel/claude_review.py \
  --diff test_diff.txt --backend heuristic

# Anthropic backend (requires ANTHROPIC_API_KEY)
python3 agents/claude-review-multimodel/claude_review.py \
  --pr https://github.com/expressjs/express/pull/6190 \
  --backend anthropic --verbose
```

## Design Philosophy

1. **Always works**: heuristic fallback means you always get a review, even in air-gapped environments
2. **Honest confidence**: heuristic reviews honestly report Low confidence — no rubber-stamping
3. **Backend choice**: swap backends to compare LLM vs heuristic output quality
4. **Structured output**: consistent Markdown format regardless of backend
5. **Zero dependencies**: stdlib-only Python, no pip install needed