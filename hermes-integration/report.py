#!/usr/bin/env python3
"""Append a one-line result to daily_log.md."""
import argparse, datetime, os

def main():
    a = argparse.ArgumentParser()
    a.add_argument("--line", required=True)
    args = a.parse_args()
    path = os.path.join(os.path.dirname(__file__), "..", "daily_log.md")
    path = os.path.normpath(path)
    stamp = datetime.date.today().isoformat()
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"| {stamp} | HERMES | {args.line} |\n")
    print(f"logged: {args.line}")


if __name__ == "__main__":
    main()
