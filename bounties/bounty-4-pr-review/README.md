# Claude Code PR Review Agent — Bounty #4

A programmatic GitHub PR diff analyzer. No AI APIs needed — it parses the diff directly and applies heuristics to detect risks and suggest improvements.

## Setup

```bash
# 1. Ensure a GitHub token is available (one of these):
export GITHUB_TOKEN="ghp_..."
# or rely on ~/.config/gh/hosts.yml (gh auth login)

# 2. Run the tool
python claude-review.py --pr https://github.com/owner/repo/pull/123
```

## Usage

```bash
# Review any public GitHub PR
python claude-review.py --pr https://github.com/python/cpython/pull/132000

# Save output to a file
python claude-review.py --pr https://github.com/rust-lang/rust/pull/141050 -o review.md
```

### Output Structure

Each review produces structured Markdown with:

| Section | Description |
|---------|-------------|
| **Summary** | Files changed, lines added/removed, file types |
| **Changed Files** | Per-file breakdown of additions/deletions |
| **Identified Risks** | Large diffs, secrets exposure, TODOs, commented-out code, binary files |
| **Improvement Suggestions** | Missing error handling, missing tests, hardcoded values, documentation |
| **Confidence Score** | 🟢 High / 🟡 Medium / 🔴 Low |

### What It Checks

- **Size heuristics**: PR too large? Too many files? Individual file too big?
- **Secrets detection**: AWS keys, GitHub tokens, OpenAI keys, private keys, passwords
- **Code quality**: TODO/FIXME markers, commented-out code
- **Missing practices**: Error handling, tests, hardcoded values, documentation
- **Binary files**: Non-reviewable binary changes

## Test Outputs

See `test_outputs/` for sample reviews of real GitHub PRs:

- `cpython_pr132000.md` — Python CPython (small, clean change — High confidence)
- `rust_lang_pr141050.md` — Rust compiler (large, multi-file change — Low confidence)
