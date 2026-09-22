"""Regenerate or verify the attributed real-PR examples without network access."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ((6731, "pr-review-1.md"), (6710, "pr-review-2.md"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Compare without changing committed files")
    args = parser.parse_args()
    env = {k: v for k, v in os.environ.items() if k not in {
        "ANTHROPIC_API_KEY", "GITHUB_TOKEN", "GH_TOKEN", "CLAUDE_REVIEW_MODEL"}}
    with tempfile.TemporaryDirectory(prefix="review-examples-") as temp:
        for number, filename in EXAMPLES:
            expected = ROOT / "examples" / filename
            output = Path(temp) / filename if args.check else expected
            fixture = ROOT / "examples" / "fixtures" / f"requests-{number}"
            command = [sys.executable, "-m", "claude_review", "--pr",
                       f"https://github.com/psf/requests/pull/{number}",
                       "--snapshot", str(fixture.with_suffix(".snapshot.json")),
                       "--response-file", str(fixture.with_suffix(".response.json")),
                       "--output", str(output)]
            result = subprocess.run(command, cwd=ROOT, env=env, check=False, timeout=30)
            if result.returncode:
                return result.returncode
            if args.check and (not expected.exists() or output.read_bytes() != expected.read_bytes()):
                print(f"FAIL: {filename} differs from the recorded execution", file=sys.stderr)
                return 1
            print(f"PASS: requests#{number} -> {filename} (recorded response; no live Claude call)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
