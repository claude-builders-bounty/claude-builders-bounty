"""Command-line interface for claude-review."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import TextIO

from . import __version__
from .core import (
    PullRef,
    ReviewError,
    load_offline,
    parse_pr_url,
    render_report,
    validate_report,
)
from .github import fetch_pull


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="claude-review",
        description="Create a deterministic, static, evidence-grounded Markdown review of a GitHub pull request.",
    )
    parser.add_argument("--pr", required=True, metavar="URL", help="https://github.com/OWNER/REPO/pull/NUMBER")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="review immutable metadata.json, files.json, and pr.diff files in --context-dir",
    )
    parser.add_argument("--context-dir", metavar="CONTEXT", help="directory containing the three offline snapshot files")
    parser.add_argument("--output", metavar="FILE", help="write Markdown to FILE instead of stdout")
    parser.add_argument("--version", action="version", version=f"claude-review {__version__}")
    return parser


def _write_output(path: str, report: str) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(report)


def main(
    argv: list[str] | None = None,
    *,
    opener=None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        ref = parse_pr_url(args.pr)
        if args.offline:
            if not args.context_dir:
                raise ReviewError("Offline mode requires --context-dir CONTEXT.")
            data = load_offline(ref, Path(args.context_dir))
        else:
            if args.context_dir:
                raise ReviewError("--context-dir is valid only with --offline.")
            data = fetch_pull(ref, opener)
        report = render_report(data)
        validate_report(report)
        if args.output:
            _write_output(args.output, report)
        else:
            stdout.write(report)
        return 0
    except ReviewError as exc:
        print(f"claude-review: error: {exc}", file=stderr)
        return getattr(exc, "exit_code", 1)
    except Exception:
        print("claude-review: error: internal review failure.", file=stderr)
        return 6


if __name__ == "__main__":
    raise SystemExit(main())
