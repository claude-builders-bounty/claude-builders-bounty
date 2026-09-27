#!/usr/bin/env python3
"""simulate.py — chạy end-to-end logic của workflow trên repo thật (không cần n8n).
Fetch GitHub API tuần qua (qua gh, đã auth) -> aggregate như Code node ->
dựng Claude prompt -> summary MOCK (không có CLAUDE_API_KEY ở đây) ->
in Discord payload sẽ gửi. Log ra samples/run-log.md làm bằng chứng test."""
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = sys.argv[1] if len(sys.argv) > 1 else "claude-builders-bounty/claude-builders-bounty"
# Demo window: repo mẫu đóng băng từ 2025 nên mặc định quét rộng để có dữ liệu thật;
# workflow production dùng $now.minus(7 days) khi chạy trên n8n.
SINCE = (sys.argv[2] if len(sys.argv) > 2
         else (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%dT00:00:00Z"))


def get(path):
    out = subprocess.run(["gh", "api", path], capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        raise SystemExit(f"gh api lỗi: {out.stderr[:200]}")
    return json.loads(out.stdout)


commits = get(f"repos/{REPO}/commits?since={SINCE}&per_page=100")
issues = [i for i in get(f"repos/{REPO}/issues?state=closed&since={SINCE}&per_page=100")
          if "pull_request" not in i]
prs = [p for p in get(f"repos/{REPO}/pulls?state=closed&per_page=100") if p.get("merged_at")]
L = [f"# Run log — {datetime.now(timezone.utc):%F %T} UTC | repo {REPO} | since {SINCE[:10]}",
     f"commits={len(commits)} closed_issues={len(issues)} merged_prs={len(prs)}", ""]
L.append("## Commits (5 đầu)")
L += ["- " + (c.get("commit", {}).get("message", "").split("\n")[0]) for c in commits[:5]] or ["- (không có)"]
L.append("## Closed issues (5 đầu)")
L += [f"- #{i['number']} {i['title']}" for i in issues[:5]] or ["- (không có)"]
L.append("## Merged PRs (5 đầu)")
L += [f"- #{p['number']} {p['title']}" for p in prs[:5]] or ["- (không có)"]
L.append("## Claude prompt (rút gọn)")
L.append(f"Write a weekly narrative dev summary (EN) for repo {REPO} ... "
         "Sections: Highlights, Merged work, Closed issues, Next-week signals. <400 words.")
L.append("## Summary (MOCK — n8n gọi Claude API thật với CLAUDE_API_KEY khi chạy)")
top = prs[0]["title"] if prs else (issues[0]["title"] if issues else "tuần yên tĩnh")
L.append(f"Highlights: {len(commits)} commits, {len(prs)} PRs merged, {len(issues)} issues closed. "
         f"Nổi bật: {top}.")
L.append("## Discord payload sẽ gửi")
L.append('{"content": "**Weekly dev summary — REPO**\\n<summary text>"}')
(HERE / "samples").mkdir(parents=True, exist_ok=True)
(HERE / "samples" / "run-log.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print("\n".join(L[:8]), "\n... -> samples/run-log.md")
