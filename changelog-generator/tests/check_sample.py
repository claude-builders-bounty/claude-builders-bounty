"""Reproduce the committed sample using an actual pinned public Git checkout."""

import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


SOURCE = Path(__file__).resolve().parents[1]
HEAD = "4e111271b1494995708a9e878a10829b5e10c7ba"
TAG_COMMIT = "ece26078ec168ebac69f02877238e68d4b376c91"
repo = Path(sys.argv[1]).resolve()


def git(*args):
    return subprocess.check_output(["git", "-C", str(repo), *args]).decode().strip()


assert git("rev-parse", "HEAD") == HEAD
assert git("rev-parse", "refs/tags/3.0.4^{commit}") == TAG_COMMIT
assert git("describe", "--tags", "--abbrev=0", HEAD) == "3.0.4"
expected_ids = git("rev-list", TAG_COMMIT + ".." + HEAD).splitlines()
assert len(expected_ids) == 22
before = git("show-ref")
python_only = os.environ.get("CHANGELOG_TEST_PYTHON_ONLY") == "1"
entry = [sys.executable, str(SOURCE / "changelog.py")] if python_only else ["bash", str(SOURCE / "changelog.sh")]
with tempfile.TemporaryDirectory(prefix="changelog-sample-") as temporary:
    output = Path(temporary) / "CHANGELOG.md"
    subprocess.run([*entry, "--repo", str(repo), "--output", str(output)], check=True)
    actual = output.read_bytes()
    assert actual == (SOURCE / "samples/CHANGELOG.markupsafe.md").read_bytes()
    ids = re.findall(r"\(`([0-9a-f]{12})`\)", actual.decode("utf-8"))
    assert len(ids) == len(set(ids)) == 22
    assert set(ids) == {value[:12] for value in expected_ids}
assert git("rev-parse", "HEAD") == HEAD and git("show-ref") == before
print("PASS: real MarkupSafe sample, 22 exact range commits, tag excluded, output bytes match, refs unchanged.")
print("Entry point: " + ("Python helper (local control)" if python_only else "actual bash changelog.sh"))
