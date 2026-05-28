#!/usr/bin/env python3
import sys
import re
BLOCK_PATTERNS = [
    r"rm\s+-[rfRF]+\s+(/|\$HOME|\~|/home|/etc|/var|/usr|/boot)",
    r"chmod\s+-[R]\s+777\s+/",
    r"mkfs\.",
    r"dd\s+.*?of=/dev/",
    r":\(\)\{ :\|:& \};:",
    r"> /dev/sd[a-z]",
    r"shutdown\s+",
    r"reboot\s+",
    r"mv\s+.*?(/etc|/var|/usr|/boot|/bin|/sbin)",
    r"cp\s+-[rfRF]+\s+(/etc|/var|/usr|/boot|/bin|/sbin)\s+",
]
WARN_PATTERNS = [
    r"cat\s+.*?(\.env|\.ssh|id_rsa)",
    r"grep\s+.*?(\.env|\.ssh|id_rsa)",
    r"curl\s+.*?169\.254\.169\.254",
    r"wget\s+.*?169\.254\.169\.254",
    r"crontab\s+",
    r"visudo",
    r"useradd",
    r"groupadd",
]
def analyze_command(command):
    for pattern in BLOCK_PATTERNS:
        if re.search(pattern, command): return "BLOCK", pattern
    for pattern in WARN_PATTERNS:
        if re.search(pattern, command): return "WARN", pattern
    return "SAFE", None
def main():
    if len(sys.argv) < 2: sys.exit(0)
    command = " ".join(sys.argv[1:])
    status, pattern = analyze_command(command)
    if status == "BLOCK":
        print(f"\n🚨 CLAUDE GUARDIAN: COMMAND BLOCKED\nTrigger: {pattern}\nCommand: {command}\n")
        sys.exit(1)
    elif status == "WARN":
        print(f"\n⚠️  CLAUDE GUARDIAN: SECURITY WARNING\nTrigger: {pattern}\nCommand: {command}\n")
        sys.exit(0)
    sys.exit(0)
if __name__ == "__main__": main()
