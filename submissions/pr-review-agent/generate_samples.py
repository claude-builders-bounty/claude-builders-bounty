"""Generate sample PR review outputs for bounty submission."""
import subprocess
import sys
from pathlib import Path

OUT = Path(__file__).parent / "samples"
PRS = [
    "https://github.com/microsoft/vscode/pull/200000",
    "https://github.com/python/cpython/pull/120000",
]

OUT.mkdir(exist_ok=True)
script = Path(__file__).parent / "claude_review.py"

for url in PRS:
    try:
        r = subprocess.run(
            [sys.executable, str(script), "--pr", url],
            capture_output=True,
            text=True,
            timeout=30,
        )
        name = url.split("/pull/")[-1].replace("/", "_") + ".md"
        (OUT / name).write_text(r.stdout if r.returncode == 0 else r.stderr, encoding="utf-8")
        print(f"ok: {name}")
    except Exception as e:
        print(f"fail {url}: {e}")
