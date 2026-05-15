# Claude Code PR Review Agent

A Claude Code sub-agent that reviews GitHub PR diffs and returns structured Markdown review comments — confidence scores, risks, and improvement suggestions included.

## 💰 Bounty: $150 (Issue #4)

Part of [claude-builders-bounty/claude-builders-bounty#4](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4).

---

## 🚀 Installation

```bash
# Clone and install
git clone https://github.com/rinopatrick/claude-builders-bounty.git
cd claude-builders-bounty

# Make executable
chmod +x claude-review
sudo cp claude-review /usr/local/bin/
```

## 🔑 Setup

Set your Anthropic API key:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

Or add to shell profile (`~/.bashrc`, `~/.zshrc`):

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

## 💬 Usage

```bash
# Review a PR
claude-review --pr https://github.com/owner/repo/pull/123

# Raw JSON output
claude-review --pr https://github.com/owner/repo/pull/123 --json
```

**Output format:**
```markdown
## 🤖 Claude Code PR Review
> 🔗 [PR URL](...)

🟢 **Confidence:** `High`

### 📋 Summary of Changes
...

### ⚠️ Identified Risks
1. ...

### 💡 Improvement Suggestions
1. ...
```

## 📁 Files

- `claude-review` — Main agent script (Python 3.10+)
- `tests/sample_review_1189.md` — Sample review on [claude-builders-bounty#1189](https://github.com/claude-builders-bounty/claude-builders-bounty/pull/1189)
- `tests/sample_review_1364.md` — Sample review on [claude-builders-bounty#1364](https://github.com/claude-builders-bounty/claude-builders-bounty/pull/1364)

## ✅ Acceptance Criteria

- [x] **CLI works:** `claude-review --pr <url>` prints structured Markdown review
- [x] **JSON mode:** `--json` flag outputs parseable JSON
- [x] **Structured output:** Summary, Risks, Suggestions, Confidence score
- [x] **Tested on 2 real PRs:** sample outputs included
- [x] **README with setup and usage:** this file

## 🧪 Tested On

| PR | Summary |
|----|---------|
| [#1189](https://github.com/claude-builders-bounty/claude-builders-bounty/pull/1189) | Security hook for blocking destructive bash commands |
| [#1364](https://github.com/claude-builders-bounty/claude-builders-bounty/pull/1364) | Dangerous bash command guard hook (Python implementation) |

Both sample reviews are in `tests/`.

## 📄 License

MIT
