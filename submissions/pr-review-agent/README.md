# claude-review — Claude Code PR Review Agent

A CLI tool that fetches a GitHub Pull Request's diff, analyzes it with Claude,
and returns a structured Markdown code review. Optionally posts the review as
a PR comment.

**No API keys required.** Uses `gh` CLI (already authenticated) and `claude`
CLI (Claude Code, authenticated via your Max plan).

---

## Requirements

| Tool | Purpose | Install |
|------|---------|---------|
| `gh` | GitHub CLI — fetch diff, post comment | [cli.github.com](https://cli.github.com) |
| `claude` | Claude Code CLI — AI analysis | [claude.ai/code](https://claude.ai/code) |
| Python 3.10+ | Run the script | system / brew / apt |

Both CLIs must be authenticated before use.

---

## Installation

```bash
# 1. Copy script to a location on your PATH
cp claude-review ~/.local/bin/claude-review
chmod +x ~/.local/bin/claude-review

# 2. Verify dependencies
gh auth status
claude --version
```

No `pip install` step needed — the script uses only Python stdlib.

---

## Usage

```bash
# Print review to stdout
claude-review --pr https://github.com/owner/repo/pull/123

# Print AND post as a PR comment
claude-review --pr https://github.com/owner/repo/pull/123 --post

# Dry-run: would post but doesn't
claude-review --pr https://github.com/owner/repo/pull/123 --post --dry-run

# Increase diff limit for large PRs (default: 80 000 bytes)
claude-review --pr https://github.com/owner/repo/pull/123 --max-diff 120000
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--pr URL` | (required) | Full GitHub PR URL |
| `--post` | off | Post review as a comment |
| `--dry-run` | off | With `--post`: print only, don't actually post |
| `--max-diff N` | 80000 | Truncate diff at N bytes |

---

## Output format

Every review contains exactly four sections:

```markdown
## PR Review

### Summary of Changes
2-3 sentences describing what changed and why.

### Identified Risks
- Concrete bugs, logic errors, edge-case failures, or breaking changes.

### Improvement Suggestions
- Actionable code-quality, readability, or design improvements.

### Confidence Score
**Confidence: High / Medium / Low**
```

**Confidence rubric:**
- **High** — diff is self-contained, all paths clear
- **Medium** — some context missing (code referenced but not in diff)
- **Low** — diff is large, heavily truncated, or domain is unfamiliar

---

## GitHub Actions

Copy `pr-review.yml` to `.github/workflows/` in your repo.
The workflow triggers on every PR open/sync/reopen event.

```yaml
# .github/workflows/pr-review.yml
# (see pr-review.yml in this directory for the full file)
```

Required secret: `CLAUDE_SESSION` — the contents of `~/.claude/session`.

---

## Sample outputs

### Review of PR #418 — "Pre-tool-use hook: blocks destructive bash commands"

<details>
<summary>Click to expand</summary>

```markdown
## PR Review

### Summary of Changes
This PR introduces a pre-tool-use hook (`safe_bash_hook.py`) that intercepts
and blocks destructive bash commands before Claude Code executes them. The hook
detects patterns like `rm -rf`, `DROP TABLE`, `git push --force`, and SQL
deletion without WHERE clauses, logs blocked attempts, and returns structured
JSON feedback to Claude. Installation is documented in README with a 2-command
setup.

### Identified Risks

- **DELETE FROM regex is overly broad**: The pattern
  `\bDELETE\s+FROM\s+\w+\s*(?:;|$)` blocks all `DELETE FROM table;` even with
  a `WHERE` clause present (if the line ends with `;`). It also fails on
  schema-qualified names (`schema.table`) and quoted identifiers. Should check
  for absence of `WHERE` explicitly.

- **rm -rf regex is fragile**: Misses variants like `rm -fR` (capital R),
  `rm -rfa`, or `rm -r -f` (space-separated flags). Consider parsing flags
  individually instead of a single regex.

- **Silent failure on JSON parse errors**: When `json.load()` fails, the hook
  silently exits with code 0, allowing the command through unchecked.

- **No protection against indirect destructive operations**: Commands like
  `mysql < destructive.sql` or `psql -c "DROP TABLE ..."` bypass the hook.

- **Unbounded log file growth**: `blocked.log` has no rotation or size limits.

- **Multiline SQL not handled**: `DELETE FROM table \n WHERE id=1` won't
  match the regex.

### Improvement Suggestions

- **Simplify rm -rf detection**: Break into a separate function that checks for
  `rm` with both `-r` and `-f` flags in any order, rather than one complex regex.

- **Fix DELETE FROM logic**: Detect absence of WHERE clause explicitly rather
  than matching the whole statement.

- **Add error handling for JSON**: Log parse errors and alert the user rather
  than silently allowing the command through.

- **Document known limitations** in README: indirect SQL through files or pipes
  is not caught.

- **Add log rotation**: Move to `.log.1` if file >10 MB.

### Confidence Score
**Confidence: Medium**

The hook functions for straightforward cases but the regex patterns have
concrete edge-case failures that could allow destructive commands through in
realistic scenarios.

---
*Review generated by [claude-review](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4)*
```

</details>

---

### Review of PR #419 — "Claude Code PR review agent — CLI + structured Markdown output"

<details>
<summary>Click to expand</summary>

```markdown
## PR Review

### Summary of Changes
Adds a new CLI tool (`claude_review.py`) that fetches GitHub PR diffs and
generates structured Markdown reviews using the Claude API. Includes a README
with setup instructions, environment variable configuration, and support for
optional auto-posting of reviews as GitHub comments.

### Identified Risks
- **No error handling for API failures**: `urllib.request.urlopen()` calls will
  raise uncaught HTTPError on auth failures, network errors, or rate limiting.
  Users see raw exceptions instead of helpful messages.
- **Hardcoded model version**: `"claude-sonnet-4-20250514"` may deprecate. No
  fallback or environment override.
- **Truncated diffs without warning**: `diff[:12000]` silently truncates large
  diffs. Users won't know if Claude is reviewing incomplete code.
- **Output format not validated**: No verification that Claude returned the
  expected Markdown format. Malformed output is printed/posted silently.
- **Encoding silent corruption**: `decode("utf-8", errors="replace")` can
  silently corrupt binary diffs. Use `errors="surrogateescape"` instead.

### Improvement Suggestions
- Wrap API calls in try/except with user-friendly error messages.
- Make model configurable via `--model` argument or `ANTHROPIC_MODEL_VERSION`
  env var.
- Log or warn when diff is truncated.
- Validate response format before printing/posting.
- Use `errors="surrogateescape"` in `decode()` to preserve binary content.
- Add exponential backoff retry for 429 errors on both GitHub and Anthropic APIs.
- Extract API calls into separate functions to improve testability.

### Confidence Score
**Confidence: High** — Code is self-contained and straightforward. All logic
paths are clear. Risks identified are edge cases, not structural problems.

---
*Review generated by [claude-review](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4)*
```

</details>

---

## Architecture

```
claude-review --pr <url>
    │
    ├── gh pr view        → PR metadata (title, author, file count)
    ├── gh pr diff        → unified diff (truncated if >80 KB)
    │
    ├── claude -p         → structured Markdown review
    │
    └── gh pr comment     → post to GitHub (with --post flag)
```

Zero external Python dependencies. All heavy lifting is delegated to two
authenticated CLIs.

---

## License

MIT
