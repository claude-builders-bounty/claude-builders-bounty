# Claude Code PR Review Sub-Agent (`claude-review`)

Analyzes any GitHub Pull Request diff via CLI or GitHub Actions and produces a structured Markdown review containing:
1. **Summary of changes** (2–3 sentences)
2. **Identified risks** (bulleted list)
3. **Improvement suggestions** (bulleted list)
4. **Confidence score** (`Low` / `Medium` / `High`)

## Setup & Usage

```bash
chmod +x claude-review.mjs
node claude-review.mjs --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/5024
```

---

## Tested Sample Output #1 (Real PR `claude-builders-bounty#5024`)

```markdown
## 🤖 Claude Code Structured PR Review: #5024

### 1. Summary of Changes
This Pull Request ("**feat(hooks): Pre-tool-use hook blocking destructive bash commands (#3)**") modifies **2 file(s)** (+**108** additions / -**0** deletions) targeting `main`. Primary touched paths include `hooks/block-destructive-bash/README.md`, `hooks/block-destructive-bash/pre_tool_use_blocker.py`.

### 2. Identified Risks
- ⚠️ `hooks/block-destructive-bash/pre_tool_use_blocker.py`: Contains shell execution or dynamic process patterns—verify input sanitization to prevent command injection.
- ⚠️ No automated test files were added or modified in this PR.

### 3. Improvement Suggestions
- 💡 Add regression unit/integration test cases covering the new code paths.

### 4. Confidence Score
**Confidence Score:** **High**
```

## Tested Sample Output #2 (Real PR `SecureBananaLabs/bug-bounty#13534`)

```markdown
## 🤖 Claude Code Structured PR Review: #13534

### 1. Summary of Changes
This Pull Request ("**feat(benchmarks): Add API benchmark suite (p50/p95/p99, TTFB, RPS) & CI regression gate (#30)**") modifies **6 file(s)** (+**262** additions / -**0** deletions) targeting `main`. Primary touched paths include `.env.benchmark`, `benchmarks/results/SUMMARY.md`, `benchmarks/run-benchmarks.mjs`, `benchmarks/thresholds.json`.

### 2. Identified Risks
- ⚠️ No automated test files were added or modified in this PR.

### 3. Improvement Suggestions
- 💡 Add regression unit/integration test cases covering the new code paths.

### 4. Confidence Score
**Confidence Score:** **High**
```
