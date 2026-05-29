#!/usr/bin/env python3
"""
pre-tool-use.py — Claude Code Pre-Tool-Use Hook
Blocks dangerous bash commands before execution.

Install: cp to ~/.claude/hooks/pre-tool-use.py
Claude Code hooks format: reads JSON from stdin, writes JSON to stdout.
"""

import sys
import json
import re

DANGEROUS_PATTERNS = [
    (r'\brm\s+(-rf|--recursive\s*--force)\b', 'rm -rf / destructive deletion'),
    (r'\bdrop\s+table\b', 'DROP TABLE — database table deletion'),
    (r'\bgit\s+push\s+(--force|\-f)\b', 'git push --force — force push'),
    (r'\btruncate\b', 'TRUNCATE — table data deletion'),
    (r'\bdelete\s+from\b(?!.*\bwhere\b)', 'DELETE FROM without WHERE clause — mass deletion'),
]

def check_dangerous(command: str):
    """Check if command matches any dangerous pattern."""
    findings = []
    for pattern, description in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            findings.append(description)
    return findings

def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            # No input — pass through
            json.dump({"result": {"proceed": True}}, sys.stdout)
            return

        data = json.loads(raw)

        # Extract the command being executed
        command = data.get("content", {}).get("text", "") or data.get("text", "") or data.get("command", "")

        if not command:
            json.dump({"result": {"proceed": True}}, sys.stdout)
            return

        findings = check_dangerous(command)
        if findings:
            # Build warning message and require confirmation
            print(f"\n⚠️  DANGEROUS COMMAND DETECTED!", file=sys.stderr)
            for f in findings:
                print(f"  • {f}", file=sys.stderr)
            print(f"\nCommand: {command[:200]}", file=sys.stderr)

            # Return blocked result — user must type 'y' to proceed
            json.dump({
                "result": {
                    "proceed": False,
                    "message": f"⚠️ Blocked by pre-tool-use hook: {'; '.join(findings)}. Type 'y' to confirm execution."
                }
            }, sys.stdout)
        else:
            json.dump({"result": {"proceed": True}}, sys.stdout)

    except json.JSONDecodeError:
        # Invalid input — pass through
        json.dump({"result": {"proceed": True}}, sys.stdout)
    except Exception as e:
        # Fail safe: allow execution if hook errors
        json.dump({"result": {"proceed": True}}, sys.stdout)

if __name__ == "__main__":
    main()
