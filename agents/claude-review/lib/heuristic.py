"""Heuristic PR analysis."""
from __future__ import annotations

import re
from typing import List

from .github_io import FileChange, Review
from .patterns import RISK_PATTERNS, SUGGEST_PATTERNS


def analyze_heuristic(meta: dict, files: List[FileChange], url: str) -> Review:
    title = meta.get("title") or "(untitled)"
    body = (meta.get("body") or "").strip()
    additions = sum(f.additions for f in files)
    deletions = sum(f.deletions for f in files)
    paths = [f.path for f in files]

    kinds = []
    if any(p.endswith((".md", ".txt", ".rst")) for p in paths):
        kinds.append("docs")
    if any(p.endswith((".py", ".ts", ".tsx", ".js", ".go", ".rs")) for p in paths):
        kinds.append("code")
    if any(".github/workflows" in p or p.endswith(".yml") for p in paths):
        kinds.append("CI")
    if any("test" in p.lower() or p.endswith("_test.py") for p in paths):
        kinds.append("tests")
    kind_s = ", ".join(kinds) or "mixed"

    summary = (
        f"This PR ({title!r}) touches {len(files)} file(s) "
        f"(+{additions}/-{deletions}) across {kind_s}. "
    )
    if body:
        paras = []
        for block in re.split(r"\n\s*\n", body):
            line = " ".join(
                ln.strip() for ln in block.splitlines()
                if ln.strip() and not ln.strip().startswith("#") and not ln.strip().startswith("- [")
            )
            if line:
                paras.append(line)
        if paras:
            first = paras[0]
            summary += f"Author notes: {first[:220]}{'…' if len(first) > 220 else ''} "
        else:
            summary += "PR description present but mostly checklist/headings. "
    else:
        summary += "No PR description was provided. "
    summary += (
        "Review focuses on security-sensitive diffs, missing tests, and maintainability."
    )

    risks: List[str] = []
    suggestions: List[str] = []
    blob = "\n".join(f.patch for f in files)

    for pat, msg in RISK_PATTERNS:
        if re.search(pat, blob, re.I):
            risks.append(msg)

    for pat, msg in SUGGEST_PATTERNS:
        if re.search(pat, blob):
            suggestions.append(msg)

    if additions + deletions > 800:
        risks.append(f"Large diff (+{additions}/-{deletions}); consider splitting for reviewability")
    if not any("test" in p.lower() for p in paths) and any(
        p.endswith((".py", ".ts", ".tsx", ".js")) for p in paths
    ):
        suggestions.append("Add or extend automated tests covering the new behavior")
    if not body:
        suggestions.append("Add a short PR description with intent and test plan")
    if any(f.status == "removed" for f in files):
        suggestions.append("Confirm removed files have no remaining imports/callers")
    if any(p.endswith("package.json") or p.endswith("package-lock.json") or p.endswith("yarn.lock") for p in paths):
        suggestions.append("Confirm lockfile is updated and CI installs the bumped version")
    if kinds == ["docs"] and additions > 80:
        suggestions.append("Keep opinionated defaults explicit; link to a minimal example repo if possible")
    if not suggestions:
        suggestions.append("Looks clean; a brief self-review note in the PR description still helps maintainers")

    score = 0
    if len(files) <= 5 and additions + deletions < 400:
        score += 1
    if body:
        score += 1
    if not risks:
        score += 1
    if kinds == ["docs"]:
        score += 1
    confidence = "High" if score >= 3 else "Medium" if score >= 1 else "Low"

    if not risks:
        risks.append("No high-severity patterns matched in the fetched patches (heuristic only)")

    def uniq(xs: List[str]) -> List[str]:
        seen = set()
        out = []
        for x in xs:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out

    return Review(
        title=title,
        url=url,
        summary=summary.strip(),
        risks=uniq(risks)[:8],
        suggestions=uniq(suggestions)[:8],
        confidence=confidence,
        files=files,
        mode="heuristic",
    )
