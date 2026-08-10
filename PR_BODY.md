## 🤖 claude-review: LLM-powered PR review sub-agent

**Closes bounty #4** — an agent that takes a PR diff as input and returns a structured Markdown review comment.

### What this is

Unlike heuristic/lint-based reviewers (regex pattern matching), this agent reads the diff **semantically** using a chat LLM (OpenAI-compatible API), so it catches real logic bugs, edge cases, and architectural issues — not just hardcoded-secret/SQL-injection patterns.

### How to Claim / Acceptance Criteria

- ✅ Works via CLI: `claude-review --pr https://github.com/owner/repo/pull/123`
- ✅ GitHub Action workflow YAML included below (in this PR description — see note)
- ✅ Structured Markdown output: Summary (2–3 sentences), Identified risks (severity-ranked), Improvement suggestions, Confidence score (Low/Medium/High)
- ✅ Tested on 2 real GitHub PRs (see `samples/`):
  - [claude-builders-bounty/claude-builders-bounty#3696](https://github.com/claude-builders-bounty/claude-builders-bounty/pull/3696) — `samples/review-pr3696.md`
  - [python/cpython#125000](https://github.com/python/cpython/pull/125000) — `samples/review-pr125000.md`
- ✅ README with setup and usage instructions
- ✅ Zero third-party dependencies (Python stdlib only)

### Sample output (real PR)

From `samples/review-pr125000.md` (cpython free-threading fix):

```markdown
### Identified Risks
- [MED] The new module-load guard uses a plain static int and atomic operations
  only under Py_GIL_DISABLED; in the GIL build it is not atomic, but since module
  exec is serialized by the import lock, this is likely safe.
- [MED] The atomic pointer load/store for curses_screen_encoding casts away const;
  the memory pointed to must remain valid, otherwise use-after-free.
- [LOW] The module-load guard sets the flag to 1 before initialization completes;
  if init fails, the module cannot be re-imported in the same process.
```

### GitHub Action workflow

Note: my automation token lacks the `workflow` scope, so I couldn't commit the workflow file into `.github/workflows/`. The workflow YAML below is ready to drop in:

```yaml
name: claude-review
on:
  pull_request:
    types: [opened, synchronize, reopened]
jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install claude-review
        run: pip install .
      - name: Run review
        run: claude-review --pr "${{ github.event.pull_request.html_url }}" --output review.md
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}
      - name: Post review comment
        run: gh pr comment "${{ github.event.pull_request.html_url }}" --body-file review.md
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Quick start

```bash
pip install .
export DEEPSEEK_API_KEY=sk-xxx   # any OpenAI-compatible endpoint works
claude-review --pr https://github.com/owner/repo/pull/123
```

### File layout

```
claude_review/
  cli.py            # CLI entrypoint
  analyzer.py       # LLM prompt + strict JSON parsing
  github_client.py  # GitHub REST client (stdlib only)
samples/            # real reviews of real PRs (acceptance evidence)
tests/              # 9 unit tests
```
