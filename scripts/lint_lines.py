#!/usr/bin/env python3
from pathlib import Path

PATHS = [Path("hooks/block_destructive_bash.py"), Path("tests/test_block_destructive_bash.py")]

for path in PATHS:
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if len(line) > 120:
            raise SystemExit(f"{path}:{number}: line is longer than 120 characters")

print("lint ok")
