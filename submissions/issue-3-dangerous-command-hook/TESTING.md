# Testing

## Local Test

```bash
python3 submissions/issue-3-dangerous-command-hook/tests.py
```

Result:

```text
tests_ok=true
```

The test runs the hook with a temporary `HOME`, verifies each required destructive pattern is denied, verifies safe Bash commands produce no hook output, and confirms blocked attempts are written to `.claude/hooks/blocked.log`.
