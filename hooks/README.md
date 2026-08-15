# Destructive Command Interceptor Hook for Claude Code

A robust, configurable bash hook designed to intercept, analyze, and block catastrophic commands before they execute in automated AI coding environments like Claude Code.

---

## ⚡ 3-Step Setup

### Step 1: Make the Hook Executable
Ensure the hook script has execute permissions:
```bash
chmod +x hooks/block-destructive.sh
```

### Step 2: Configure Claude Code Hook
Integrate `block-destructive.sh` into your Claude Code settings or PreToolUse hook configuration.

Add to your project's `.claude/config.json` (or `~/.claude/config.json` for global protection):
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "command": "./hooks/block-destructive.sh $TOOL_INPUT"
      }
    ]
  }
}
```

*Alternative Shell Wrapper Setup:*
If using Claude Code in a custom bash environment or subshell, alias or wrap your command runner:
```bash
run_safe() {
  ./hooks/block-destructive.sh "$@" && eval "$@"
}
```

### Step 3: Verify the Protection
Test that the hook properly blocks catastrophic commands while allowing valid dev workflows:
```bash
# Verify dangerous command is blocked (returns exit code 1)
./hooks/block-destructive.sh "rm -rf /"

# Verify safe build/cleanup command passes (returns exit code 0)
./hooks/block-destructive.sh "rm -rf node_modules dist"
```

---

## 🛡️ What It Blocks

| Category | Blocked Examples | Allowed Safe Equivalents |
|---|---|---|
| **File Deletions** | `rm -rf /`, `rm -rf ~`, `rm -rf *`, `rm -rf ..` | `rm -rf node_modules`, `rm -rf dist`, `rm -rf .next`, `rm file.txt` |
| **Git Operations** | `git push -f origin main`, `git push --force origin master` | `git push origin feat/branch`, `git push -f origin feat/my-feature` |
| **Disk Overwrites** | `mkfs.ext4 /dev/sda1`, `dd if=/dev/zero of=/dev/sda` | `dd if=/dev/urandom of=./test.bin bs=1M count=10` |
| **Permissions** | `chmod -R 777 /`, `chown -R root:root /etc` | `chmod +x ./build.sh`, `chmod -R 755 ./public` |
| **Database Actions** | `DROP DATABASE production;`, `TRUNCATE TABLE users;` | `SELECT * FROM users;`, `CREATE TABLE test (...)` |
| **System Shutdowns** | `shutdown -h now`, `init 0`, `reboot`, fork bombs | `pm2 restart app`, `systemctl status nginx` |

---

## ⚙️ Custom Configuration & Overrides

### Adding Custom Block Rules
Open `hooks/block-destructive.sh` and add specific regex patterns in the designated section. For instance, to block AWS S3 bucket deletion:
```bash
if echo "$COMMAND_STR" | grep -iE '\baws[[:space:]]+s3[[:space:]]+rb[[:space:]]+.*--force' >/dev/null 2>&1; then
    block_command "AWS S3 force bucket deletion detected"
fi
```

### Bypassing in Controlled Environments
If you legitimately need to run a restricted command in a sandboxed CI runner:
1. Set an environment variable override (if configured):
   ```bash
   ALLOW_DESTRUCTIVE_COMMANDS=1 ./my-script.sh
   ```
2. Or invoke the command directly in an isolated Docker container rather than on the host.

---

## 🧪 Running Automated Tests
Run the comprehensive test suite to validate all 20+ edge cases and rules:
```bash
chmod +x tests/test_hook.sh
./tests/test_hook.sh
```
