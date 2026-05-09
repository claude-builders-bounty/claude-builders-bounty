"""Helper that dumps a 'screenshot' of the imported n8n workflow as
text — used by the bounty deliverable to capture verifiable evidence
the workflow loads into a real n8n instance.

The maintainer can re-run this on their own machine after `n8n import:workflow`
to confirm.

    python dump_n8n_state.py [--db PATH] [--out FILE]

Defaults to %N8N_USER_FOLDER%/database.sqlite when N8N_USER_FOLDER is set.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--db",
        default=None,
        help="Path to n8n's SQLite database (default: $N8N_USER_FOLDER/database.sqlite)",
    )
    p.add_argument(
        "--out",
        default=None,
        help="Write the report to this file (default: stdout)",
    )
    args = p.parse_args()

    db_path = args.db or os.path.join(
        os.environ.get("N8N_USER_FOLDER", str(Path.home() / ".n8n")),
        "database.sqlite",
    )
    if not Path(db_path).exists():
        sys.stderr.write(f"error: n8n DB not found at {db_path}\n")
        return 1

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT id, name, active, nodes, connections FROM workflow_entity")
    rows = cur.fetchall()

    out_lines = []
    out_lines.append(f"# n8n verification — local instance state")
    out_lines.append("")
    out_lines.append(f"- Database file: `{db_path}`")
    out_lines.append(f"- Workflows imported: **{len(rows)}**")
    out_lines.append("")

    for wf_id, wf_name, active, nodes_json, conn_json in rows:
        nodes = json.loads(nodes_json) if isinstance(nodes_json, str) else nodes_json
        connections = json.loads(conn_json) if isinstance(conn_json, str) else conn_json
        out_lines.append(f"## Workflow: `{wf_id}` — {wf_name}")
        out_lines.append("")
        out_lines.append(f"- Active: `{bool(active)}`")
        out_lines.append(f"- Node count: **{len(nodes)}**")
        out_lines.append("")
        out_lines.append("### Nodes (in graph layout order)")
        out_lines.append("")
        out_lines.append("| Position | Type | Name | Notes |")
        out_lines.append("|---|---|---|---|")
        for n in nodes:
            pos = n.get("position", [0, 0])
            note = (n.get("notes") or "").replace("|", "\\|").replace("\n", " ")
            note = (note[:60] + "…") if len(note) > 60 else note
            out_lines.append(f"| {pos[0]:>4}, {pos[1]:>4} | `{n['type']}` | {n['name']} | {note} |")
        out_lines.append("")

        # Render connections as an edge list
        out_lines.append("### Connections (graph edges)")
        out_lines.append("")
        for src, ports in (connections or {}).items():
            for branches in ports.get("main", []) or []:
                for tgt in branches:
                    out_lines.append(f"- `{src}` → `{tgt['node']}` (port {tgt.get('index', 0)})")
        out_lines.append("")

    report = "\n".join(out_lines).rstrip() + "\n"
    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
        sys.stderr.write(f"wrote {args.out}\n")
    else:
        sys.stdout.write(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
