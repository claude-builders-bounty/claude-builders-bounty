#!/usr/bin/env python3
"""json_to_csv.py — Convert a JSON array of flat objects into a CSV file.

Usage:
    python json_to_csv.py input.json output.csv

Behavior:
    - Reads a JSON file containing an array of flat objects.
    - The CSV header is the union of all keys across every object,
      preserving first-seen order for stable, predictable output.
    - Missing keys are filled with an empty string.
    - Values are stringified; None becomes an empty string.

Exit codes:
    0 success, 1 usage error, 2 input/parse error.
"""
from __future__ import annotations

import csv
import json
import sys
from typing import Any


def collect_fieldnames(records: list[dict[str, Any]]) -> list[str]:
    """Union of keys across all records, in first-seen order."""
    fieldnames: list[str] = []
    seen: set[str] = set()
    for rec in records:
        for key in rec:
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)
    return fieldnames


def normalize(value: Any) -> str:
    """Render a JSON value as a CSV cell."""
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        # Flat objects are expected, but degrade gracefully.
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def json_to_csv(records: list[dict[str, Any]], out_handle) -> int:
    """Write records to out_handle as CSV. Returns row count written."""
    if not isinstance(records, list):
        raise ValueError("Top-level JSON must be an array of objects.")
    fieldnames = collect_fieldnames(records)
    writer = csv.DictWriter(out_handle, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for rec in records:
        if not isinstance(rec, dict):
            raise ValueError("Every array element must be a JSON object.")
        writer.writerow({k: normalize(rec.get(k, "")) for k in fieldnames})
    return len(records)


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        sys.stderr.write("Usage: python json_to_csv.py input.json output.csv\n")
        return 1
    in_path, out_path = argv[1], argv[2]
    try:
        with open(in_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        sys.stderr.write(f"Error: input file not found: {in_path}\n")
        return 2
    except json.JSONDecodeError as e:
        sys.stderr.write(f"Error: invalid JSON: {e}\n")
        return 2
    try:
        with open(out_path, "w", encoding="utf-8", newline="") as f:
            n = json_to_csv(data, f)
    except ValueError as e:
        sys.stderr.write(f"Error: {e}\n")
        return 2
    sys.stdout.write(f"Wrote {n} row(s) to {out_path}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
