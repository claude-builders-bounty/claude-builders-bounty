# -*- coding: utf-8 -*-
import subprocess
import os
import sys
import io

def test_generator():
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("Testing Changelog Generator...")

    # We can't easily mock git log without a repo, but we can test the logic
    # if we refactor the generator to accept messages directly.
    # For now, let's just run it on the current repo as a smoke test.

    cmd = ["python", "generator.py", "--version", "1.0.0"]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")

    print("Output Snippet:")
    print("\n".join(result.stdout.splitlines()[:15]))

    assert "## [1.0.0]" in result.stdout
    assert "Features" in result.stdout or "Bug Fixes" in result.stdout or "Other" in result.stdout

    print("Test passed!")

if __name__ == "__main__":
    test_generator()
