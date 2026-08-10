#!/usr/bin/env python3
"""claude-review：Claude Code PR 审查子代理。

用法：
  python3 claude_review.py --pr https://github.com/owner/repo/pull/123
  python3 claude_review.py --pr owner/repo/pull/123 --backend codex   # 可选 LLM 后端
  python3 claude_review.py --pr owner/repo/pull/123 --json

默认使用内置启发式分析（无需 API Key）；--backend codex|claude 时把 diff 交给
Codex CLI / Claude CLI 做语义审查。
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def gh(args: list[str]) -> str:
    r = subprocess.run(["gh", "api", *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"gh api 失败：{r.stderr.strip()}")
    return r.stdout


def parse_pr(ref: str) -> tuple[str, str, int]:
    ref = ref.replace("https://github.com/", "").strip("/")
    parts = ref.split("/")
    if len(parts) == 4 and parts[2] == "pull":
        return parts[0], parts[1], int(parts[3])
    if len(parts) == 3 and parts[2].isdigit():
        return parts[0], parts[1], int(parts[2])
    raise ValueError(f"无法解析 PR 引用：{ref}")


def heuristic_review(title: str, files: list[dict]) -> dict:
    risks: list[str] = []
    suggestions: list[str] = []
    total_added = 0
    total_removed = 0
    changed = [f["filename"] for f in files]
    patch_text = "\n".join(f.get("patch", "") for f in files)

    for f in files:
        total_added += int(f.get("additions", 0))
        total_removed += int(f.get("deletions", 0))

    # 风险模式
    secret_pat = re.compile(r"(api[_-]?key|password|secret|token)\s*[:=]\s*['\"][^'\"]+['\"]", re.IGNORECASE)
    if secret_pat.search(patch_text):
        risks.append("疑似硬编码密钥/口令（api_key/password/secret/token）")
    if re.search(r"\bconsole\.log\b|\bdebugger\b", patch_text):
        risks.append("遗留 console.log / debugger 调试代码")
    if re.search(r"\bTODO\b|\bFIXME\b", patch_text, re.IGNORECASE):
        risks.append("存在未完成标记（TODO/FIXME）")
    if re.search(r"\beval\s*\(|\bexec\s*\(|subprocess\.(shell=True)", patch_text):
        risks.append("存在动态执行/不安全 shell 调用")
    if re.search(r"(\bSELECT\b.*\bFROM\b|\bDELETE\b|\bUPDATE\b).*\+|f['\"].*SELECT", patch_text, re.IGNORECASE):
        risks.append("SQL 字符串拼接风险（疑似注入面）")
    if any(f.endswith(".env") or ".env." in f for f in changed):
        risks.append(".env 文件进入版本库")
    if total_added > 800:
        risks.append(f"单 PR 新增 {total_added} 行，过大，建议拆分")
    if not any(re.search(r"test|spec", f, re.IGNORECASE) for f in changed):
        suggestions.append("未发现测试文件变更，建议补充覆盖核心逻辑的测试")
    if not re.search(r"README|docs/", "\n".join(changed), re.IGNORECASE):
        suggestions.append("如属新功能，建议同步更新文档")
    if total_removed == 0 and total_added > 0:
        suggestions.append("纯新增，确认是否有应清理的冗余/旧路径")

    # 摘要
    areas = sorted({f.split("/")[0] for f in changed if "/" in f})
    areas_text = "、".join(areas[:5]) if areas else "根目录"
    summary = (
        f"本 PR 共改动 {len(changed)} 个文件（+{total_added}/-{total_removed} 行），"
        f"主要涉及 {areas_text}。"
    )
    confidence = "High" if total_added < 300 else ("Medium" if total_added < 800 else "Low")

    return {
        "summary": summary,
        "risks": risks,
        "suggestions": suggestions,
        "confidence": confidence,
        "files": len(changed),
        "added": total_added,
        "removed": total_removed,
    }


def llm_review(title: str, diff: str, backend: str) -> dict:
    prompt = (
        "You are a senior code reviewer. Review the following GitHub PR diff.\n"
        f"PR title: {title}\n\n"
        "Output in this exact Markdown structure:\n"
        "## Summary of changes\n(2-3 sentences)\n"
        "## Identified risks\n- list\n"
        "## Improvement suggestions\n- list\n"
        "## Confidence score: Low/Medium/High\n\n"
        "DIFF:\n" + diff[:60000]
    )
    if backend == "codex":
        r = subprocess.run(
            ["codex", "exec", "--sandbox", "read-only", prompt],
            capture_output=True, text=True, timeout=300,
        )
    else:
        r = subprocess.run(["claude", "-p", prompt], capture_output=True, text=True, timeout=300)
    return {"raw": r.stdout.strip(), "confidence": "Medium", "backend": backend}


def render_markdown(title: str, url: str, r: dict) -> str:
    if "raw" in r:
        return f"# PR Review: {title}\n\n来源：{url}\n\n" + r["raw"]
    lines = [
        f"# PR Review: {title}",
        "",
        f"来源：{url} ｜ 审查时间：{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "## Summary of changes",
        "",
        r["summary"],
        "",
        "## Identified risks",
        "",
    ]
    lines += [f"- [ ] {x}" for x in (r["risks"] or ["未发现明显风险"])]
    lines += ["", "## Improvement suggestions", ""]
    lines += [f"- {x}" for x in (r["suggestions"] or ["无"])]
    lines += ["", f"## Confidence score: {r['confidence']}", ""]
    lines += [f"- 改动文件 {r['files']} 个，+{r['added']}/-{r['removed']} 行"]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Claude Code PR reviewer")
    ap.add_argument("--pr", required=True, help="PR 链接或 owner/repo/pull/N")
    ap.add_argument("--backend", choices=["heuristic", "codex", "claude"], default="heuristic")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    owner, repo, num = parse_pr(args.pr)
    meta = json.loads(gh([f"repos/{owner}/{repo}/pulls/{num}"]))
    files = json.loads(gh([f"repos/{owner}/{repo}/pulls/{num}/files?per_page=100"]))
    title = meta.get("title", f"PR #{num}")
    url = meta.get("html_url", args.pr)

    if args.backend == "heuristic":
        result = heuristic_review(title, files)
    else:
        diff = "\n".join(f.get("patch", "") for f in files)
        result = llm_review(title, diff, args.backend)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(title, url, result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
