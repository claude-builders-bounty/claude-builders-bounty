#!/usr/bin/env python3
"""
claude-review  –  PR-Review-Agent (Claude Code)
Prüft einen GitHub-PR und gibt eine strukturierte Review als Markdown aus.

Nutzung:
  python claude-review.py --pr https://github.com/owner/repo/pull/123
  python claude-review.py --pr owner/repo#123   (ohne https://)
  python claude-review.py --pr https://github.com/envoyproxy/envoy/pull/33079 --output review.md
"""

import argparse, json, os, re, subprocess, sys, textwrap, urllib.request

# ── Konstanten ────────────────────────────────────────────────────────────────
GITHUB_API   = "https://api.github.com"
DEFAULT_MODEL = "claude-sonnet-4-20250514"
MAX_DIFF_CHARS = 60_000  # Claude kann bis ~100k Token verarbeiten

# ── GitHub-API-Hilfen ────────────────────────────────────────────────────────

def gh(method, path, **kwargs):
    token = os.environ.get("GITHUB_TOKEN", "")
    h = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json", "User-Agent": "claude-review/1.0"}
    return requests.request(method, f"{GITHUB_API}{path}", headers=h, timeout=30, **kwargs)

def parse_pr_spec(spec: str) -> tuple[str, int]:
    """'owner/repo#123' oder 'https://github.com/owner/repo/pull/123' → (owner/repo, 123)"""
    m = re.match(r"https?://github\.com/([^/]+/[^/]+)/pull/(\d+)", spec)
    if m:
        return m.group(1), int(m.group(2))
    m = re.match(r"^([^/]+/[^/]+)#(\d+)$", spec)
    if m:
        return m.group(1), int(m.group(2))
    raise ValueError(f"Kann PR-Spezifikation nicht parsen: {spec}")

def get_pr_diff(full_repo: str, pr_num: int) -> str:
    """Hole Unified-Diff der PR."""
    r = gh("get", f"/repos/{full_repo}/pulls/{pr_num}")
    if r.status_code != 200:
        raise SystemExit(f"❌ PR nicht gefunden: {r.status_code}")
    pr = r.json()
    head_sha = pr["head"]["sha"]

    # Diff zwischen Base und Head
    r2 = gh("get", f"/repos/{full_repo}/compare/{pr['base']['sha']}...{head_sha}",
            headers={"Accept": "application/vnd.github.v3.diff"})
    if r2.status_code != 200:
        raise SystemExit(f"❌ Diff nicht abrufbar: {r2.status_code}")

    diff = r2.text
    if len(diff) > MAX_DIFF_CHARS:
        print(f"⚠️  Diff ist zu groß ({len(diff):,} Zeichen). Schneide auf {MAX_DIFF_CHARS:,} zu.")
        diff = diff[:MAX_DIFF_CHARS]
    return diff

def get_pr_context(full_repo: str, pr_num: int) -> dict:
    r = gh("get", f"/repos/{full_repo}/pulls/{pr_num}")
    pr = r.json()
    return {
        "title": pr["title"],
        "body": pr.get("body", ""),
        "author": pr["user"]["login"],
        "additions": pr["additions"],
        "deletions": pr["deletions"],
        "changed_files": pr["changed_files"],
    }

# ── Hauptfunktion ─────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Claude Code PR-Review-Agent")
    p.add_argument("--pr", required=True, help="PR-URL oder owner/repo#123")
    p.add_argument("--output", "-o", help="Schreibe Review in Datei (sonst stdout)")
    p.add_argument("--model", default=DEFAULT_MODEL, help="Claude-Modell (Standard: sonnet)")
    p.add_argument("--json", action="store_true", help="Gib nur das JSON zurück")
    args = p.parse_args()

    full_repo, pr_num = parse_pr_spec(args.pr)
    print(f"🔍 Analyse PR: {full_repo} #{pr_num}")
    print("   Hole Diff …", flush=True)

    diff = get_pr_diff(full_repo, pr_num)
    ctx = get_pr_context(full_repo, pr_num)

    print(f"   Diff: {len(diff):,} Zeichen, {ctx['additions']} additions, {ctx['deletions']} deletions")
    print("   Sende an Claude …\n", flush=True)

    # Claude API aufrufen
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not anthropic_key:
        sys.exit("❌ ANTHROPIC_API_KEY Umgebungsvariable fehlt.\n   export ANTHROPIC_API_KEY=sk-ant-...")

    prompt = f"""You are an experienced code reviewer. Analyse the following GitHub Pull Request and return a structured Markdown review.

PR: {ctx['title']}
Author: @{ctx['author']}
Stats: +{ctx['additions']} / -{ctx['deletions']} ({ctx['changed_files']} files changed)
URL: https://github.com/{full_repo}/pull/{pr_num}

---
Diff (unified format):
{diff}
---

Return your review in this exact Markdown format:

## 📋 Summary
[2–3 sentences describing the purpose and scope of the changes]

## ⚠️ Risks
- [Potential issue 1 — explain briefly]
- [Potential issue 2]
(Use '-' bullets. If none, write "No significant risks identified.")

## 💡 Suggestions
- [Improvement 1 — concrete and actionable]
- [Improvement 2]
(Use '-' bullets. If no improvements, write "No improvements suggested.")

## 🎯 Confidence
**Confidence Score:** Low / Medium / High
[1‑sentence rationale for your confidence level]

Do NOT include any additional sections beyond these four headers."""

    payload = {
        "model": args.model,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    }

    r_claude = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": anthropic_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json=payload, timeout=120,
    )

    if r_claude.status_code != 200:
        print(f"❌ Claude API Fehler: {r_claude.status_code}")
        print(r_claude.text[:300])
        sys.exit(1)

    review = r_claude.json()["content"][0]["text"]
    print(review)

    if args.output:
        with open(args.output, "w") as f:
            f.write(review + "\n")
        print(f"\n✅ Review gespeichert: {args.output}")


if __name__ == "__main__":
    main()
