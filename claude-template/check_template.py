#!/usr/bin/env python3
"""Fail when a path mentioned in CLAUDE.md is missing from a sample app."""
import pathlib
import re
import sys

ROOT = pathlib.Path(sys.argv[1]).resolve()
DOC = pathlib.Path(__file__).with_name("CLAUDE.md").read_text(encoding="utf-8")
paths = sorted(set(re.findall(r"(?:app|components|lib|db|data)/[A-Za-z0-9_./()-]+(?<![.])", DOC)))
missing = [rel for rel in paths if not (ROOT / rel).exists()]
print(f"paths={len(paths)} missing={len(missing)}")
for rel in missing:
    print("MISSING", rel)
sys.exit(1 if missing else 0)
