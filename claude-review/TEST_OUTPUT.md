# Test Output: claude-review

## Test Run — 2026-07-17

### Test 1: URL Parsing
```
PASS: https://github.com/anthropics/anthropic-sdk-python/pull/100 -> ('anthropics', 'anthropic-sdk-python', 100)
PASS: github.com/owner/repo/pull/42 -> ('owner', 'repo', 42)
PASS: owner/repo#99 -> ('owner', 'repo', 99)
PASS: https://www.github.com/org/project/pull/1 -> ('org', 'project', 1)
```

### Test 2: CLI Interface
```
claude-review --help: PASS
```

### Test 3: Fetch Real PRs

**PR #1: anthropics/anthropic-sdk-python#100**
- Title: chore(internal): update mypy to v1.4.1
- Author: stainless-bot
- Files: 2 (poetry.lock, pyproject.toml)
- Diff: 8,894 chars
- Status: PASS

**PR #2: python/cpython#117000**
- Title: gh-92906: Enable test_cext and test_cppext on Windows
- Author: vstinner
- Files: 7
- Diff: 16,502 chars
- Status: PASS

### Test 4: CLI Flags
```
--json flag: PRESENT
-o flag: PRESENT
--model flag: PRESENT
```

### Test 5: Python API
```python
from claude_review import review_pr
review = review_pr("owner", "repo", 123)
```
Status: PASS (function importable and callable)

---

All tests passed. The tool successfully:
1. Parses PR URLs in multiple formats
2. Fetches PR metadata and diffs from GitHub API
3. Exposes --json, -o, and --model CLI flags
4. Can be invoked as `claude-review <url>` or `python -m claude_review`
