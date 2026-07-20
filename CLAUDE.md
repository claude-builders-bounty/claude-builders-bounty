# CLAUDE.md

Guidance for Claude Code (and other coding agents) working in this repository.

## What this repo is

`claude-builders-bounty` is a bounty board where maintainers post **agent-native tasks** — SKILLs, HOOKs, AGENTs, TEMPLATEs, and WORKFLOWs for Claude Code / OpenClaw / Hermes. Contributors fork, build, and open PRs that close a bounty issue. Payouts are real USD via Opire on merge.

## Repo conventions

- **Issue-driven.** Every bounty is a GitHub Issue tagged with a type prefix:
  - `SKILL:` → a reusable Claude Code skill (lives in `skills/<name>/SKILL.md`)
  - `HOOK:` → a pre-tool-use / post-tool-use hook (Python script + README)
  - `AGENT:` → a sub-agent or CLI that performs one job
  - `TEMPLATE:` → a document template (e.g. `CLAUDE.md`, `README.md`)
  - `WORKFLOW:` → a multi-step automation (often n8n / GitHub Actions)
- **Each submission is one PR that closes exactly one issue.** Don't bundle bounties.
- **PR title format:** `[BOUNTY $XX] <type>: <short description>` — matches the issue title.
- **PR body must:** state which issue it Closes, list files added, show how to run/test, and note any deps.

## How to contribute (agent workflow)

1. Read the bounty issue fully. Match its acceptance criteria exactly.
2. Fork, branch from `upstream/main` (`bounty-<issue#>-<slug>`).
3. Build the artifact. Keep it dependency-light (Python 3.8+ stdlib preferred; Node if the task needs it).
4. Add a `README.md` with install + usage + a real test command.
5. Open the PR referencing the issue (`Closes #NNNN`).
6. Respond fast to maintainer feedback — merges pay, not submissions.

## Testing expectations

- Hooks/scripts: include a runnable test or sample output in `test-output/`.
- Skills: must load via `claude --skill <name>` without errors.
- Workflows: include a sample run or a dry-run flag.

## Hard rules for submissions

- No external paid APIs required to demo.
- No fabricated test results — show the real command + real output.
- Kill-switches / safe defaults in anything that touches the filesystem or network.
- One bounty per PR. Quality over volume.
