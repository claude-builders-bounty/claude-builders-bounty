# claude-pr-reviewer

A Claude Code sub-agent that reviews a GitHub pull request and posts a structured Markdown comment.

Built for [claude-builders-bounty issue #4](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4).

---

## What it does

- Fetches the PR diff and metadata via `gh` CLI
- Sends the diff to Claude with a structured review prompt
- Returns a Markdown comment covering: summary, verdict, per-finding issues (with file + line), checklist, and stats
- Optionally posts the comment directly to the PR

## Two ways to use it

### 1. As a Claude Code sub-agent (recommended)

Copy `.claude/agents/pr-reviewer.md` into your project's `.claude/agents/` directory:

```bash
cp .claude/agents/pr-reviewer.md your-project/.claude/agents/
```

Then in Claude Code, just say:

```
review PR #42
```

or

```
check PR #42 and post a comment
```

Claude Code will automatically invoke the `pr-reviewer` sub-agent. It will:
1. Fetch the diff with `gh pr diff 42`
2. Analyse it
3. Post a structured comment to the PR

### 2. As a standalone CLI script

**Requirements:**
- Python 3.10+
- `anthropic` package: `pip install anthropic`
- `gh` CLI, authenticated: `gh auth login`
- `ANTHROPIC_API_KEY` environment variable set

**Usage:**

```bash
# Review a PR and print to terminal
python claude_review.py 42

# Review and post as a GitHub comment
python claude_review.py 42 --post

# Review a PR in a different repo
python claude_review.py 42 --repo myorg/myrepo --post

# Save the review to a file
python claude_review.py 42 --output review.md
```

## Example output

```markdown
## 🤖 Automated PR Review

> Reviewed by pr-reviewer · PR #42 · Fix null pointer in user lookup

---

### Summary

The PR adds a guard clause for a missing `user_id`, preventing a null-pointer
error at the database layer. The change is minimal and well-targeted.

**Verdict:** ⚠️ Approve with suggestions

---

### Issues

#### 🔵 Low — Missing test for None case

**File:** `tests/test_user.py` (line 45)  
**Problem:** The new guard clause raises `ValueError` for `None`, but there's no test
covering this path.  
**Suggested fix:**
```python
def test_get_user_none_id_raises():
    with pytest.raises(ValueError, match="user_id must not be None"):
        get_user(None)
```

---

### Checklist

| | Item |
|---|---|
| ❌ | New code has corresponding tests |
| ✅ | Error cases are handled |
| ✅ | No secrets or credentials in code |
| ✅ | Changes are backward-compatible |
| ✅ | Commit messages are clear |

---

<details>
<summary>Stats</summary>

- Files changed: 2
- Additions: +15 / Deletions: -3
- Findings: 0 critical, 0 high, 0 medium, 1 low, 0 suggestions

</details>
```

## Running the tests

```bash
python -m unittest tests.test_claude_review
```

Expected output:
```
..........
----------------------------------------------------------------------
Ran 10 tests in 0.05s

OK
```

## File structure

```
.
├── .claude/
│   └── agents/
│       └── pr-reviewer.md   ← Claude Code sub-agent definition
├── tests/
│   └── test_claude_review.py
├── claude_review.py          ← standalone CLI
└── README.md
```

## Requirements

- Python 3.10+
- `anthropic>=0.25.0`
- `gh` CLI (for posting comments)
