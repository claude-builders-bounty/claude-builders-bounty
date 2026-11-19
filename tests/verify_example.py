"""Reproduce the pinned real GitHub history example without network access."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]


def verify(print_output=False):
    metadata = json.loads((ROOT / "example/provenance.json").read_text())
    bundle = ROOT / "example/vec.bundle"
    assert hashlib.sha256(bundle.read_bytes()).hexdigest() == metadata["bundle_sha256"]
    with tempfile.TemporaryDirectory() as temporary:
        repo = Path(temporary) / "vec sample"
        subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "-c", "init.defaultBranch=main", "clone", "--quiet", str(bundle), str(repo)], check=True)
        head = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
        tag = subprocess.check_output(["git", "-C", str(repo), "describe", "--tags", "--abbrev=0", "HEAD"], text=True).strip()
        tag_commit = subprocess.check_output(["git", "-C", str(repo), "rev-parse", f"refs/tags/{tag}^{{commit}}"], text=True).strip()
        assert (head, tag, tag_commit) == (metadata["head"], metadata["tag"], metadata["tag_commit"])
        # Follow the documented setup: check tools, copy the two files, invoke bash.
        for command in [["git", "--version"], ["python3", "--version"], ["bash", "--version"]]:
            subprocess.run(command, check=True, capture_output=True)
        for name in ["changelog.sh", "generate_changelog.py"]:
            (repo / name).write_bytes((ROOT / name).read_bytes())
        result = subprocess.run(["bash", "changelog.sh"], cwd=repo, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        assert result.stderr == "", result.stderr
        assert result.stdout == f"Wrote {repo / 'CHANGELOG.md'}\n", result.stdout
        output = (repo / "CHANGELOG.md").read_bytes()
        if print_output:
            print(output.decode(), end="")
            return
        assert output == (ROOT / "example/CHANGELOG.md").read_bytes(), "sample output differs"
        print(f"Real GitHub sample reproduced: {metadata['repository']} at {head}")
        print(f"Range: {tag_commit}..{head}; stdout/status and README setup checked")
        print(f"CHANGELOG.md SHA256: {hashlib.sha256(output).hexdigest()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--print-output", action="store_true", help="print generated sample for inspection")
    args = parser.parse_args()
    verify(args.print_output)
