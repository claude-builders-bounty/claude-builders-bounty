#!/usr/bin/env python
"""Read-only forensics over Hermes' own state.db for the auto-skill-distill job.

Why this exists: every distill run so far hand-rolled throwaway probes and three of
them tripped the same traps (silent-zero epoch comparison, guessed columns, counting
the run's own session). This script encodes the traps away.

Usage
  python scripts/scan_sessions.py                 # 7-day inventory + new-material verdict + signatures
  python scripts/scan_sessions.py --days 14       # wider window
  python scripts/scan_sessions.py --tables        # dump schema (sessions / messages)
  python scripts/scan_sessions.py --sql "select source, count(*) from sessions group by source"
  python scripts/scan_sessions.py --json out.json # machine-readable dump

Exit codes: 0 = scanned, 3 = no new material since the last non-cron session
"""
import argparse
import collections
import json
import os
import re
import sqlite3
import sys
import time

DEFAULT_SIGS = {
    # label: regex
    "approval_block": r"(script execution via -e/-c|execute_code runs arbitrary|approval timeout)",
    "edit_refused_partial": r"offset/limit pagination",
    "edit_refused_modified": r"modified since you last read",
    "patch_non_exact": r"Non-exact match",
    "syntax_error": r"(IndentationError|SyntaxError):",
    "quote_mangling": r"(unterminated string literal|unexpected EOF while looking for matching)",
    "sql_schema_guess": r"OperationalError: no such (column|table)",
    "subprocess_encoding": r"(UnicodeDecodeError|UnicodeEncodeError): '?(gbk|cp936|utf-8|charmap)",
    "timeout": r"(Command timed out|timed out after \d)",
    "rate_limit": r"(\b429\b|rate limit|quota exceeded)",
    "stream_error": r"(ProviderStreamError|StreamError|ReadError)",
    "kanban_body_edit": r"kanban edit[^\n]{0,40}--body",
    "stale_write": r"(" + "|".join(["refusing to overwrite", "task has not seen its full current content"]) + r")",
}


def resolve_db(explicit=None):
    cands = []
    if explicit:
        cands.append(explicit)
    home = os.environ.get("HERMES_HOME")
    if home:
        cands.append(os.path.join(home, "state.db"))
    cands += [
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))))), "state.db"),  # <hermes_home>/skills/devops/auto-skill-distill/scripts/
        os.path.expanduser("~/.hermes/state.db"),
        r"D:/Ai/Agent/hermes/state.db",
    ]
    for c in cands:
        if c and os.path.isfile(c):
            return os.path.normpath(c)
    sys.exit("state.db not found; pass --db PATH")


def connect(path):
    if not os.path.isfile(path):
        sys.exit("state.db missing: %s" % path)
    con = sqlite3.connect("file:%s?mode=ro" % path.replace("\\", "/"), uri=True, timeout=10)
    con.row_factory = sqlite3.Row
    return con


def to_epoch(v):
    """started_at is stored as REAL epoch on current builds but has been TEXT on
    older ones. Parse both, never let a type mismatch silently drop every row."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    try:
        return float(s)
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return time.mktime(time.strptime(s[:26], fmt))
        except ValueError:
            continue
    return None


def fmt(ts):
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(ts)) if ts else "?"


def dump_tables(con):
    names = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    print("tables (%d): %s" % (len(names), ", ".join(names)))
    for t in ("sessions", "messages"):
        if t in names:
            cols = [r[1] for r in con.execute("PRAGMA table_info(%s)" % t)]
            print("\n%s (%d cols):\n  %s" % (t, len(cols), ", ".join(cols)))


def inventory(con, days, include_current, active_min):
    now = time.time()
    cutoff = now - days * 86400
    rows = []
    for r in con.execute("SELECT id, source, started_at, message_count, tool_call_count, title, cwd FROM sessions"):
        ep = to_epoch(r["started_at"])
        if ep is None or ep < cutoff:
            continue
        rows.append({"id": r["id"], "source": r["source"], "epoch": ep,
                     "messages": r["message_count"] or 0, "tool_calls": r["tool_call_count"] or 0,
                     "title": r["title"] or "", "cwd": r["cwd"] or ""})
    # drop this run's own session: a cron session started minutes ago is us, not material
    current = [r for r in rows if r["source"] == "cron" and (now - r["epoch"]) < active_min * 60] if not include_current else []
    cur_ids = {r["id"] for r in current}
    rows = [r for r in rows if r["id"] not in cur_ids]
    rows.sort(key=lambda r: r["epoch"])
    return rows, current, cutoff


def signatures(con, ids, sigs):
    if not ids:
        return {}
    ph = ",".join("?" * len(ids))
    compiled = {k: re.compile(v) for k, v in sigs.items()}
    cnt = {k: [0, set()] for k in sigs}
    q = "SELECT session_id, role, tool_name, content FROM messages WHERE session_id IN (%s)" % ph
    for r in con.execute(q, ids):
        c = r["content"] or ""
        for k, p in compiled.items():
            if p.search(c):
                cnt[k][0] += 1
                cnt[k][1].add(r["session_id"])
    return {k: {"messages": v[0], "sessions": len(v[1])} for k, v in cnt.items() if v[0]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db")
    ap.add_argument("--days", type=float, default=7)
    ap.add_argument("--tables", action="store_true")
    ap.add_argument("--sql")
    ap.add_argument("--json")
    ap.add_argument("--include-current", action="store_true")
    ap.add_argument("--active-min", type=int, default=30, help="cron sessions younger than N minutes count as THIS run")
    ap.add_argument("--no-sigs", action="store_true")
    a = ap.parse_args()

    db = resolve_db(a.db)
    con = connect(db)
    print("db: %s" % db)
    kind = con.execute("SELECT typeof(started_at) FROM sessions WHERE started_at IS NOT NULL LIMIT 1").fetchone()
    print("started_at storage type: %s  (compare as epoch, never as ISO text)" % (kind[0] if kind else "?"))

    if a.tables:
        dump_tables(con)
        return 0
    if a.sql:
        q = a.sql.strip()
        if not re.match(r"(?is)^(select|pragma|with|explain)\b", q):
            sys.exit("read-only guard: query must start with select/pragma/with/explain")
        cur = con.execute(q)
        cols = [d[0] for d in cur.description] if cur.description else []
        if cols:
            print(" | ".join(cols))
        for row in cur.fetchall():
            print(" | ".join("" if v is None else str(v) for v in row))
        return 0

    rows, current, cutoff = inventory(con, a.days, a.include_current, a.active_min)
    for c in current:
        print("excluded (this run): %s  started %s" % (c["id"], fmt(c["epoch"])))
    print("window: %s -> now (%g days) · sessions=%d · messages=%d"
          % (fmt(cutoff), a.days, len(rows), sum(r["messages"] for r in rows)))
    by = collections.Counter(r["source"] for r in rows)
    print("by source: %s" % dict(by))
    for r in rows:
        print("  %-40s %-8s %s %5d msgs %4d calls | %s"
              % (r["id"][:40], r["source"], fmt(r["epoch"]), r["messages"], r["tool_calls"], r["title"][:60]))

    newest = rows[-1] if rows else None
    fresh = [r for r in rows if r["source"] != "cron"]
    distill_runs = [r for r in rows if r["source"] == "cron" and r["title"].startswith("auto-skill-distill")]
    last_distill = max(distill_runs, key=lambda r: r["epoch"]) if distill_runs else None
    newest_fresh = max(fresh, key=lambda r: r["epoch"]) if fresh else None
    # A previous run of THIS job having analysed everything newer than the newest
    # human/worker session means there is no new material — only gaps.
    if last_distill and newest_fresh and newest_fresh["epoch"] <= last_distill["epoch"]:
        verdict = "NO NEW MATERIAL"
    elif not newest_fresh:
        verdict = "NO NEW MATERIAL"
    else:
        verdict = "NEW MATERIAL"
    print("\nlast distill run in window: %s (%s)" % (last_distill["id"] if last_distill else "none",
                                                     fmt(last_distill["epoch"]) if last_distill else "-"))
    print("newest non-cron session:   %s (%s)" % (newest_fresh["id"] if newest_fresh else "none",
                                                  fmt(newest_fresh["epoch"]) if newest_fresh else "-"))
    print("VERDICT: %s — if NO NEW MATERIAL, only fill uncovered gaps or reply [SILENT]" % verdict)

    result = {"db": db, "days": a.days, "sessions": rows, "verdict": verdict}
    if not a.no_sigs:
        sig = signatures(con, [r["id"] for r in rows], DEFAULT_SIGS)
        print("\n=== signature counts (msgs / sessions) ===")
        for k, v in sorted(sig.items(), key=lambda kv: -kv[1]["sessions"]):
            flag = "CANDIDATE" if v["sessions"] >= 3 else "below threshold"
            print("  %-22s %4d / %-3d  %s" % (k, v["messages"], v["sessions"], flag))
        result["signatures"] = sig
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=1)
        print("\nwrote %s" % a.json)
    return 3 if verdict == "NO NEW MATERIAL" else 0


if __name__ == "__main__":
    sys.exit(main())
