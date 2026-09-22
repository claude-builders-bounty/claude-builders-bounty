#!/usr/bin/env python3
"""claude-review — structured PR review agent (Opire bounty #4)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

# Allow `python3 claude_review.py` from this directory
sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.engine import (  # noqa: E402
    analyze_heuristic,
    fetch_pr,
    load_diff_file,
    parse_pr_ref,
    refine_with_claude,
    render_markdown,
)


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(prog="claude-review", description="Structured PR review agent")
    p.add_argument("--pr", help="GitHub PR URL or owner/repo#N")
    p.add_argument("--diff", help="Local unified diff path (offline)")
    p.add_argument("--title", default="Local diff", help="Title when using --diff")
    p.add_argument("--url", default="(local)", help="Canonical URL when using --diff")
    p.add_argument("--json", action="store_true", help="Emit JSON instead of Markdown")
    p.add_argument("--no-llm", action="store_true", help="Force heuristic mode even if API key set")
    args = p.parse_args(argv)

    if not args.pr and not args.diff:
        p.error("Provide --pr or --diff")

    if args.pr:
        owner, repo, number = parse_pr_ref(args.pr)
        meta, files = fetch_pr(owner, repo, number)
        url = meta.get("html_url") or f"https://github.com/{owner}/{repo}/pull/{number}"
        review = analyze_heuristic(meta, files, url)
    else:
        files = load_diff_file(args.diff)
        meta = {"title": args.title, "body": ""}
        review = analyze_heuristic(meta, files, args.url)

    if not args.no_llm:
        review = refine_with_claude(review, files)

    if args.json:
        print(
            json.dumps(
                {
                    "title": review.title,
                    "url": review.url,
                    "summary": review.summary,
                    "risks": review.risks,
                    "suggestions": review.suggestions,
                    "confidence": review.confidence,
                    "mode": review.mode,
                    "files": [
                        {
                            "path": f.path,
                            "status": f.status,
                            "additions": f.additions,
                            "deletions": f.deletions,
                        }
                        for f in review.files
                    ],
                },
                indent=2,
            )
        )
    else:
        print(render_markdown(review))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
