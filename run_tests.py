#!/usr/bin/env python3
"""Run hook unit tests without pytest dependency."""

import subprocess
import sys
from pathlib import Path

TESTS = Path(__file__).parent / "tests" / "test_block_destructive_commands.py"


def main() -> int:
    try:
        import pytest  # noqa: F401
    except ImportError:
        # Fallback: import and run test functions directly
        sys.path.insert(0, str(Path(__file__).parent))
        import tests.test_block_destructive_commands as t

        failures = 0
        for name in sorted(dir(t)):
            if not name.startswith("test_"):
                continue
            try:
                getattr(t, name)()
                print(f"PASS {name}")
            except Exception as exc:
                failures += 1
                print(f"FAIL {name}: {exc}")
        return 1 if failures else 0

    proc = subprocess.run(
        [sys.executable, "-m", "pytest", str(TESTS), "-q"],
        check=False,
    )
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
