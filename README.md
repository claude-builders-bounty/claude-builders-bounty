# Claude Builders Bounty Tools 🛠️

A collection of high-performance tools and skills for Claude Code and agentic workflows.

## 1. 📝 CHANGELOG Generator
Automatically generate a structured `CHANGELOG.md` from git history.

### Setup (3 Steps):
1. **Clone**: `git clone https://github.com/mvmax-dev/claude-builders-bounty.git`
2. **Permissions**: `chmod +x changelog.sh`
3. **Run**: `./changelog.sh`

---

## 2. 🛡️ Security Hook
Intercepts and blocks dangerous bash commands before execution.

### Installation:
1. Create hooks dir: `mkdir -p ~/.claude/hooks`
2. Copy script: `cp security_hook.py ~/.claude/hooks/pre-tool-use.py`

---

## 3. 📝 PR Reviewer
Automated PR review and feedback logic.
Run: `python3 pr_reviewer.py`
