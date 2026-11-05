# claude-review — PR Review Agent

Takes a GitHub PR as input, analyzes the diff, and produces a structured Markdown review.

## Usage (3 steps)

```bash
# 1. Set your token
export GITHUB_TOKEN=ghp_...

# 2. Run it (3 ways)
python claude_review.py --pr https://github.com/owner/repo/pull/123
python claude_review.py --pr owner/repo#123
python claude_review.py --repo owner/repo --number 123

# 3. Save to file or post as comment
python claude_review.py --pr owner/repo#123 --output review.md
python claude_review.py --pr owner/repo#123 --post
```

## Structured Output

| Section | Content |
|---------|---------|
| **Summary** | 2–3 sentence overview with file count, +/− lines, primary language |
| **Risks** | Hardcoded secrets, eval/exec, unbounded loops, catch-all excepts, TODO/FIXME, debug code, force pushes, etc. |
| **Suggestions** | File count/lines thresholds, missing tests per new file, sensitive filenames |
| **Confidence** | 🟢 High / 🟡 Medium / 🔴 Low — based on risk count + PR size |

## Detected Risk Patterns

| Pattern | What it catches |
|---------|----------------|
| `hardcoded-secret` | API keys, tokens, passwords committed in source |
| `eval-or-exec` | `eval()`, `exec()`, `subprocess.call`, `os.system`, `shell=True` |
| `unbounded-loop` | `while True:` without break visible |
| `catch-all-except` | Bare `except:` (hides bugs) |
| `db-no-transaction` | 3+ sequential DML without transaction hints |
| `no-input-validation` | `request.args`, `request.json` access without zod-like validation |
| `TODO-FIXME` | Reminders left in production code |
| `force-push` | `force=True` or `--force` in git ops |
| `debug-code` | `console.log`, `print()`, `debugger;` |

## Sample outputs

Two sample reviews included: `sample_review_1.md` and `sample_review_2.md`.
