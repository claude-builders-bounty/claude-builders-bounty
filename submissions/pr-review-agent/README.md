# PR Review Agent

A CLI tool that reviews GitHub Pull Requests and outputs structured Markdown analysis. No API keys or LLM calls required -- pure pattern-based analysis using only `gh` (GitHub CLI) and standard shell utilities.

**Bounty**: [#4 - AGENT: PR reviewer with structured Markdown output](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4)

---

## What It Does

`claude-review.sh` takes a GitHub PR URL, fetches the diff and metadata via the GitHub CLI, and produces a structured Markdown review containing:

- **Summary** -- 2-3 sentences describing the PR (files changed, lines added/removed, change type)
- **Stats table** -- quick-glance metrics
- **Files changed** -- per-file additions/deletions breakdown
- **Identified risks** -- pattern-matched issues like hardcoded secrets, debug statements, missing error handling, eval/exec usage, and more
- **Improvement suggestions** -- actionable recommendations (add tests, update docs, clean up debug code, etc.)
- **Confidence score** -- Low / Medium / High with a 0-100 numeric score and full breakdown

---

## Setup

### Prerequisites

1. **GitHub CLI** (`gh`) -- install from [cli.github.com](https://cli.github.com/)
2. **Authenticated session** -- run `gh auth login` to authenticate
3. **Bash** -- works on Linux, macOS, Windows (Git Bash/WSL)

No additional dependencies. No API keys. No Python, Node, or other runtimes needed.

### Installation

```bash
# Clone the repo (or just download the script)
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
cd claude-builders-bounty/submissions/pr-review-agent
```

---

## Usage

### Basic usage (outputs to stdout)

```bash
bash claude-review.sh https://github.com/owner/repo/pull/123
```

### Save to file

```bash
bash claude-review.sh --output review.md https://github.com/owner/repo/pull/123
```

### Show help

```bash
bash claude-review.sh --help
```

---

## Sample Output

> Reviewed PR: [cli/cli#13119](https://github.com/cli/cli/pull/13119) -- "Document dependency CVE policy in SECURITY.md"

```markdown
# PR Review: Document dependency CVE policy in SECURITY.md

> **PR**: #13119 in cli/cli
> **Author**: @BagToad | **State**: MERGED
> **Branch**: kw/security-md-dep-cve-policy -> trunk

---

## Summary

This PR adds code across 1 file(s) with +2/-0 line changes (XS (trivial)).
Updates 1 documentation file(s). Touches 1 config/CI file(s).

## Identified Risks

- No significant risks detected.

## Improvement Suggestions

- PR looks well-structured. No additional suggestions.

## Confidence Score

| Score | Level |
|-------|-------|
| 100/100 | High |
```

Full sample outputs are available in the [`samples/`](./samples/) directory.

---

## How Scoring Works

The confidence score starts at **100** and is adjusted based on detected patterns.

### Size Penalties

| PR Size | Total Lines Changed | Penalty |
|---------|-------------------|---------|
| XS (trivial) | < 50 | 0 |
| Small | 50 - 199 | 0 |
| Medium | 200 - 499 | -5 |
| Large | 500 - 999 | -15 |
| XL (very large) | 1000+ | -25 |

### Risk Penalties

| Pattern | Per Occurrence |
|---------|---------------|
| Hardcoded secrets/credentials | -15 |
| Security features disabled | -15 |
| eval/exec (code injection) | -12 |
| Large file changes (>500 lines) | -10 |
| Empty/weak error handling | -8 |
| Debug statements (console.log, print) | -5 |
| TODO/FIXME/HACK markers | -3 |

### Good Pattern Bonuses

| Pattern | Bonus |
|---------|-------|
| Test files included | +10 |
| Documentation updated | +5 |
| Type annotations added | +5 |

### Final Score Mapping

| Score Range | Confidence Level |
|-------------|-----------------|
| 75 - 100 | High |
| 40 - 74 | Medium |
| 0 - 39 | Low |

---

## Detected Patterns

### Risk Patterns (scanned on added lines only)

- **Hardcoded secrets**: `api_key=`, `password:`, `token=`, `credential=`, `private_key=`
- **Debug statements**: `console.log`, `console.debug`, `print(`, `debugger`, `binding.pry`, `pdb.set_trace`
- **TODO markers**: `TODO`, `FIXME`, `HACK`, `XXX`, `WORKAROUND`
- **Empty error handling**: `catch {}`, `except:`, `except Exception:`, `.catch(() =>`
- **Code injection**: `eval(`, `exec(`, `Function(`
- **Security bypass**: `verify=false`, `disable ssl`, `insecure`, `no-verify`
- **Environment access**: `process.env.`, `os.environ`, `getenv(`

### Good Patterns

- **Tests**: files matching `test`, `spec`, or `__tests__` in the path
- **Documentation**: files with `.md`, `.rst`, `.txt`, `.doc` extensions
- **Type annotations**: TypeScript types, Python type hints, interface/type declarations
- **Config/CI**: `.yml`, `.yaml`, `.toml`, `.json`, `Dockerfile`, `.github/` files

---

## Architecture

```
claude-review.sh
  |
  +-- Parse PR URL (owner/repo/number)
  +-- Verify gh CLI + auth
  +-- Fetch PR diff (gh pr diff)
  +-- Fetch PR metadata (gh pr view --json --jq)
  +-- Pattern analysis
  |     +-- Risk detection (grep on added lines)
  |     +-- Good pattern detection (file list matching)
  |     +-- File classification
  +-- Score calculation
  +-- Markdown generation
  +-- Output (stdout or file)
```

All JSON extraction uses `gh --jq` built-in support. No external JSON parsers needed.

---

## License

MIT
