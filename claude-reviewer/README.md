# claude-review — Claude Code sub-agent for PR reviews

A zero-dependency Python 3 CLI / Claude Code sub-agent that takes a GitHub Pull Request
(`--pr <url>`) or any unified diff (`--diff <file>` or `stdin`), analyzes the change, and
prints a **structured Markdown review comment**:

1. `### Summary of Changes` — 2–3 sentences
2. `### Identified Risks` — severity-tagged list with `file:line` references
3. `### Improvement Suggestions` — actionable remediation items
4. `### Confidence Score` — `Low` / `Medium` / `High` with a one-line justification

## Why it is reliable

The agent has two engines:

| Engine | When it runs | What it does |
|---|---|---|
| **Claude API** | `ANTHROPIC_API_KEY` is set | Sends diff + static pre-check to the Anthropic Messages API, parses the JSON review |
| **Deterministic static analyzer** | always (and as fallback) | Pure-Python regex/heuristic analysis: hardcoded secrets, SQL injection, `shell=True`/`os.system`, `eval`/`exec`, bare `except`, disabled TLS verification, leftover debug statements, unresolved `TODO`/`FIXME`, missing test coverage, oversized patches |

If the API key is missing, the network is down, or the model returns malformed JSON, the
static engine still produces a complete, correctly formatted review — so CI never breaks
and a review is always posted.

## Requirements

- Python 3.8+ (standard library only — **no `pip install` required**)
- Optional: `ANTHROPIC_API_KEY` for the LLM engine
- Optional: `GITHUB_TOKEN` for private repositories and `--post-comment`

## Setup

```bash
git clone <this repo> && cd claude-reviewer
chmod +x claude_review.py
python3 --version   # 3.8+
```

## Usage

### 1. Review a live GitHub PR

```bash
export ANTHROPIC_API_KEY="sk-ant-..."   # optional
export GITHUB_TOKEN="ghp_..."           # optional, raises rate limit / private repos

python3 claude_review.py --pr https://github.com/owner/repo/pull/123
```

Add `--post-comment` to publish the review straight onto the PR:

```bash
python3 claude_review.py --pr https://github.com/owner/repo/pull/123 --post-comment
```

### 2. Review a local diff (no network)

```bash
git diff | python3 claude_review.py --diff -
python3 claude_review.py --diff changes.patch --title "feat: add retry helper"
```

### 3. Machine-readable output / file output

```bash
python3 claude_review.py --pr <url> --format json
python3 claude_review.py --diff changes.patch -o review_comment.md
```

### 4. Run the test suite

```bash
python3 -m unittest discover -s . -p "test_*.py" -v
```

10 tests cover URL parsing, unified-diff parsing (new/modified/deleted files), each risk
detector, missing-test detection, Markdown structure, mocked GitHub/Anthropic API calls
and the CLI flags.

## CLI reference

| Flag | Description |
|---|---|
| `--pr <url>` | GitHub PR URL (`https://github.com/owner/repo/pull/N`) |
| `--diff <path\|->` | Unified diff file, or `-` for stdin |
| `--title <text>` | PR title for local diffs (improves the summary) |
| `--format markdown\|json` | Output format (default `markdown`) |
| `--output/-o <path>` | Write output to a file |
| `--post-comment` | Post the review to the PR (needs `--pr` + `GITHUB_TOKEN`) |
| `--model <id>` | Claude model (default `claude-3-7-sonnet-latest`, or `CLAUDE_MODEL`) |

Exit codes: `0` success, `1` runtime/API error, `2` no input provided.

## GitHub Action

`.github/workflows/claude-review.yml` runs the tests, reviews every opened/updated PR,
and comments the result. Add `ANTHROPIC_API_KEY` as a repository secret to enable the LLM
engine (the static engine is used when the secret is absent).

## Sample outputs

Real runs against two public PRs, generated with `python3 claude_review.py --pr <url>`:

- `sample-outputs/sample_reviews.md` — Flask `pallets/flask#6168` and a feature PR from
  `claude-builders-bounty/claude-builders-bounty#4918`

## Design notes

- `parse_unified_diff()` tracks old/new line numbers per hunk, so every finding carries the
  exact post-change line number; binary files, renames and `/dev/null` sides are handled.
- Findings are deduplicated on `(file, category, line)` and sorted `High → Medium → Low`,
  capped at 8 items so the comment stays readable.
- Missing-test detection compares changed implementation files against changed test files
  (`test_*`, `*_test.py`, `*.spec.ts`, …) and only fires when no test file changed.
- Confidence is downgraded to `Medium` for very large diffs (>800 changed lines), where
  diff-local analysis cannot see cross-module effects.
- `to_markdown()` enforces the 2–3 sentence summary and the `Low/Medium/High` enum, so the
  contract holds even if one engine yields unexpected values.

## License

MIT — matches the parent repository.
