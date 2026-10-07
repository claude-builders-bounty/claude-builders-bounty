# claude-review — PR review sub-agent CLI

Static, rule-based pull-request reviewer that fetches any GitHub PR and produces a
structured Markdown review in milliseconds. **No AI, no third-party dependencies** —
pure Python 3.7+ standard library.

Resolves [#1412](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1412)
(bounty: AGENT — PR reviewer with structured Markdown output).

## What it produces

Every review is a Markdown document with four sections:

| Section | Content |
|---|---|
| **Summary** | PR intent, author, change profile (files, +/- lines, language mix) |
| **Risk Assessment** | Findings table with severity: `CRITICAL` / `HIGH` / `MEDIUM` / `LOW` |
| **Suggestions** | Actionable next steps, prioritised by what the heuristics found |
| **Confidence** | 0–100 score derived from patch coverage and scanability |

Sample outputs produced by this exact build, run on two real PRs from this
repository: [`tests/review-1398.md`](tests/review-1398.md) and
[`tests/review-1409.md`](tests/review-1409.md).

## Setup

```bash
# nothing to install — single file, stdlib only
git clone https://github.com/laojinpassion/claude-builders-bounty.git
cd claude-builders-bounty/claude-review

chmod +x claude-review        # optional, for ./claude-review invocation
python claude-review --help
```

Works with Python 3.7+ on Linux / macOS / Windows (no compilation, no pip install).

### GitHub token (recommended, optional)

Unauthenticated GitHub API allows 60 requests/hour per IP; a token raises it to
5,000/hour. The tool never requires one for public repos:

```bash
export GITHUB_TOKEN=ghp_xxx    # optional; read from the environment only
```

The token is read from the environment, never written to disk, never sent anywhere
except `api.github.com`.

## Usage

```bash
python claude-review --pr https://github.com/owner/repo/pull/123   # full URL
python claude-review --pr owner/repo#123                            # shorthand
python claude-review --pr owner/repo#123 --output review.md         # write to file

echo $?   # 0 = clean, 1 = CRITICAL findings found (CI-friendly), 2/3 = input/API errors
```

## What it checks

All heuristics run locally against the PR's added lines:

- **Hardcoded secrets** — OpenAI/GitHub/AWS-style keys, private key blocks, credential-shaped assignments, bearer tokens (always `CRITICAL`)
- **Dangerous execution** — `shell=True`, `os.system`, `eval`/`exec`, `pickle.load`, unsafe `yaml.load`, `child_process.exec`, dynamic `Function()`
- **Injection surfaces** — SQL built via f-string/`%`/`+` concatenation, `innerHTML`/`dangerouslySetInnerHTML`
- **Destructive SQL** — `DROP TABLE`, `TRUNCATE`, `DELETE` without `WHERE`
- **Weak crypto / bad randomness** — `md5`/`sha1`, `random` used where CSPRNG is expected
- **Network hygiene** — outbound HTTP calls without explicit timeout
- **High-risk locations** — auth/payment/migration/infra paths, CI workflow edits, dependency manifest changes
- **Hygiene** — test deletions, debug-output splatter, committed TODO/FIXME markers

### False-positive suppression

Raw pattern matching alone drowns security tooling in noise — a guard hook
*contains* dangerous strings by design. `claude-review` adjusts severity by context:

- Pattern literals inside **comments** or **docs** → `LOW` (pattern reference)
- Quoted literals in source (likely pattern definitions, e.g. blocklist entries) → `MEDIUM`
- Bare statements in `.sql` files or unquoted code → `HIGH`
- Secret patterns are **never** downgraded — a real key in a comment is still a leak

Measured on PR [#1409](https://github.com/claude-builders-bounty/claude-builders-bounty/pull/1409)
(a destructive-command guard hook): naive matching reports 7 HIGH findings; with
context suppression the same patch yields 1 MEDIUM + 2 LOW with zero false HIGH —
see [`tests/review-1409.md`](tests/review-1409.md).

## Confidence scoring

```
confidence = patch_coverage × 80      # share of changed files whose patch was scannable
           + 10 (all files scanned) or 5 (partial)
           capped at 98
```

Binary files and oversized patches (>20 KB) are listed as unscanned so a human
knows where the blind spots are.

## Limitations

This is a **static pre-review filter, not a replacement for human review**. It can
miss semantic bugs, cross-file logic issues, and anything expressible only by
running the code. Use it to triage the 90% mechanical part of review so humans can
spend attention on the 10% that needs judgement.
