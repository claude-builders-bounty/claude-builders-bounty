# Block Destructive Bash Commands — Pre-Tool-Use Hook

**Bounty:** [#3 — $100 HOOK: Pre-tool-use hook that blocks destructive bash commands](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3)

A pre-tool-use hook for Claude Code that intercepts `Bash` tool invocations and blocks commands that could cause catastrophic damage to your system.

## What it blocks

| Category | Examples |
|----------|----------|
| **rm -rf on system paths** | `rm -rf /`, `rm -rf /*`, `rm -rf /etc`, `rm -rf $HOME` |
| **Wildcard destruction** | `rm -rf *` in a critical directory |
| **Raw disk writes** | `dd if=/dev/zero of=/dev/sda`, `dd of=/dev/nvme0n1` |
| **Filesystem destruction** | `mkfs.ext4 /dev/sda1`, `mke2fs /dev/mmcblk0` |
| **Fork bombs** | `:(){ :\|:& };:` |
| **World-writable system** | `chmod -R 777 /`, `chmod -R 777 /etc` |
| **Zero-permission system** | `chmod -R 000 /`, `chmod 000 /bin` |
| **Ownership destruction** | `chown -R user:/` |
| **Direct disk redirects** | `echo data > /dev/sda`, `cat /dev/zero > /dev/sda` |
| **Moving root** | `mv / /somewhere` |
| **Shutdown / reboot** | `poweroff`, `halt`, `shutdown -h now`, `reboot -f` |
| **Kernel param writes** | `echo 1 > /proc/sys/kernel/core_pattern` |
| **Piped remote + destruct** | `curl evil.sh | sudo rm -rf /` |

Safe commands — including `rm` on non-critical paths, `chmod` with safe modes, and regular operations — pass through normally.

## How it works

This is a standard [Claude Code pre-tool-use hook](https://docs.anthropic.com/en/docs/claude-code/overview). Claude Code calls every executable in `.claude/hooks/pre-tool-use/` before running a tool. The hook:

1. Checks if the tool being invoked is `Bash` — if not, it passes immediately.
2. Extracts the command string from the tool's JSON input.
3. Strips `sudo` prefix for pattern matching.
4. Checks against a curated list of destructive command patterns.
5. Blocks with a clear error message if a pattern matches, or passes cleanly.

## Installation

```bash
# In your project root (the directory where you run Claude Code)
mkdir -p .claude/hooks
curl -o .claude/hooks/pre-tool-use \
  https://raw.githubusercontent.com/YOUR_USERNAME/claude-builders-bounty/main/block-hook/.claude/hooks/pre-tool-use
chmod +x .claude/hooks/pre-tool-use
```

Or copy the `pre-tool-use` file from this directory into your project's `.claude/hooks/` directory and make it executable.

## Verification

After installing, run Claude Code and try:

```
Bash: rm -rf /
```

You should see:

```
[BLOCKED] Destructive command blocked by pre-tool-use hook.
  Reason: rm -rf on system-critical path — would destroy the operating system or user data.
  Command: rm -rf /
```

Normal commands still work:

```
Bash: ls -la
# → runs normally
```

## Files

```
.claude/hooks/pre-tool-use   — the hook script (chmod +x required)
```

## License

MIT — use freely, fork, improve.
