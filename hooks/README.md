# Claude Code Pre-Tool-Use Hook: Destructive Command Guard

Implements **Opire Bounty #3 ($100)** for `claude-builders-bounty`.

An offline, robust pre-tool-use hook that intercepts and blocks dangerous commands before execution by Claude Code or automated agents.

## Features
- **Strict Pattern Matching**: Intercepts:
  - Recursive forced file deletions (`rm -rf`, `rm -fr`, `--recursive --force`)
  - Git force pushes (`git push --force`, `-f`, `+refs/`)
  - SQL DDL destruction (`DROP TABLE`, `DROP DATABASE`, `DROP SCHEMA`, `DROP VIEW`)
  - Table truncations (`TRUNCATE TABLE`)
  - Unbounded SQL deletes (`DELETE FROM <table>` without `WHERE`)
  - Low-level disk formatting (`dd of=/dev/...`, `mkfs.*`)
- **Audit Logging**: Every blocked attempt is recorded with ISO-8601 timestamp, offending command, and reason in `~/.claude/hooks/blocked.log`.
- **Exit Code Convention**: Exits `2` on blocked commands to halt agent execution, `0` when safe.

## Installation into Claude Code
1. Copy `hooks/block-destructive-bash.sh` to your local hooks directory:
   ```bash
   mkdir -p ~/.claude/hooks
   cp hooks/block-destructive-bash.sh ~/.claude/hooks/pre-tool-use.sh
   chmod +x ~/.claude/hooks/pre-tool-use.sh
   ```

2. Test execution:
   ```bash
   bash tests/test_block_destructive.sh
   ```

## Opire Bounty Payout Details
- **Bounty**: #3 ($100 USD)
- **Recipient**: @huyhoang2k5
- **USDC (Base / EVM)**: `0xa57a66df3c7053FDAb5fD1d72040bc0c5b3455F8`
- **PayPal**: `lnhhoang2k5@gmail.com`
