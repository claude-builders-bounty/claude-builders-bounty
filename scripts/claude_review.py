#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
claude-review — Claude Code PR reviewer sub-agent.

Usage:
  claude-review --pr https://github.com/owner/repo/pull/123

Fetches a public PR diff via the GitHub REST API (no auth required for public repos),
analyzes it, and prints a structured Markdown review comment to stdout:
  - Summary of changes (2-3 sentences)
  - Identified risks (list)
  - Improvement suggestions (list)
  - Confidence score: Low / Medium / High

Read-only: never writes to the PR, never mutates the repository.
"""
import argparse
import json
import re
import sys
import urllib.request
import urllib.error
from typing import Dict, List, Tuple


def parse_pr_url(url: str) -> Tuple[str, str, int]:
    """Extract (owner, repo, pull_number) from a GitHub PR URL."""
    m = re.search(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not m:
        raise ValueError(f"不支持的 PR URL 格式: {url}")
    return m.group(1), m.group(2), int(m.group(3))


def _get(url: str) -> Dict:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "claude-review/1.0",
        },
    )
    with urllib.request.urlopen(req, timeout=40) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_pr(owner: str, repo: str, pull_number: int) -> Dict:
    return _get(f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}")


def fetch_pr_files(owner: str, repo: str, pull_number: int) -> List[Dict]:
    """Fetch PR files (includes unified `patch` per file)."""
    return _get(f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/files")


def classify_risk(diff_text: str) -> List[str]:
    """Heuristic risk identification from the unified diff."""
    risks: List[str] = []
    low = diff_text.lower()

    if re.search(r"(secret|password|api_key|token|private_key)", low):
        risks.append("疑似在新增行中硬编码敏感信息（密码/密钥/token），应改用环境变量或密钥管理。")
    if re.search(r"\b(eval|exec|system|popen|subprocess)\b", low):
        risks.append("存在动态代码执行调用（eval/exec/system/popen/subprocess），需确认输入已严格校验。")
    if re.search(r"\b(DELETE|UPDATE|INSERT|DROP|TRUNCATE)\b", low):
        risks.append("涉及数据库写入/删除/修改，建议增加事务边界与 WHERE 子句审计。")
    if re.search(r"\b(rm -rf|unlink)\b", low):
        risks.append("涉及文件删除操作，建议增加保护性检查与备份确认。")
    if re.search(r"(http|fetch|axios|requests)", low):
        risks.append("新增外部网络请求，建议加超时、重试与响应校验。")

    if not risks:
        risks.append("未检测到明显高风险模式（基于启发式扫描）。")
    return risks


def suggest_improvements(diff_text: str, files: List[Dict]) -> List[str]:
    """Generate improvement suggestions from the diff."""
    suggestions: List[str] = []
    added_lines = [l for l in diff_text.splitlines() if l.startswith("+") and not l.startswith("+++")]
    added_text = "\n".join(added_lines)

    if any(f.get("filename", "").endswith((".ts", ".tsx")) for f in files):
        suggestions.append("TypeScript 文件：确认新增代码已加显式类型注解，避免 `any`。")
    if "test" in added_text.lower() or "__tests__" in diff_text:
        suggestions.append("检测到测试相关变更，确认新增功能已配套单元/集成测试。")
    if any("api" in f.get("filename", "").lower() for f in files):
        suggestions.append("API 路由变更：确认已加 Zod 输入校验与统一错误返回形状。")
    if re.search(r"(console\.log|print|debugger)", added_text):
        suggestions.append("新增行中出现调试输出（console.log/print/debugger），建议移除或改用结构化日志。")

    if not suggestions:
        suggestions.append("代码变更整体简洁，保持现有命名与结构约定即可。")
    return suggestions


def confidence_score(risks: List[str], files: List[Dict], additions: int) -> str:
    """Low / Medium / High confidence."""
    high_risk = any(r.startswith(("疑似", "存在", "涉及")) for r in risks)
    if high_risk or additions > 500 or len(files) > 10:
        return "Low"
    if additions > 100 or len(files) > 3:
        return "Medium"
    return "High"


def build_review(pr: Dict, files: List[Dict]) -> str:
    additions = sum(f.get("additions", 0) for f in files)
    deletions = sum(f.get("deletions", 0) for f in files)
    diff_text = "\n".join(f.get("patch", "") or "" for f in files)
    risks = classify_risk(diff_text)
    suggestions = suggest_improvements(diff_text, files)
    confidence = confidence_score(risks, files, additions)

    title = pr.get("title", "")
    body = pr.get("body") or ""
    changed = [f.get("filename", "") for f in files][:12]

    lines: List[str] = []
    lines.append("## PR 审查摘要")
    lines.append("")
    lines.append(f"- **PR**: #{pr.get('number')} {title}")
    lines.append(f"- **仓库**: {pr.get('base', {}).get('repo', {}).get('full_name', '')}")
    lines.append(f"- **文件数**: {len(files)} | **新增**: {additions} 行 | **删除**: {deletions} 行")
    lines.append("")
    lines.append("### 变更概述")
    lines.append("")
    summary = (body[:400] + ("…" if len(body) > 400 else "")) if body else "无 PR 描述，基于 diff 推断。"
    lines.append(summary)
    lines.append("")
    lines.append("涉及文件（前 12 个）：")
    for f in changed:
        lines.append(f"- `{f}`")
    lines.append("")
    lines.append("### 风险识别")
    lines.append("")
    for r in risks:
        lines.append(f"- {r}")
    lines.append("")
    lines.append("### 改进建议")
    lines.append("")
    for s in suggestions:
        lines.append(f"- {s}")
    lines.append("")
    lines.append(f"### 置信度分数：{confidence}")
    lines.append("")
    lines.append("*由 `claude-review` 自动生成（基于启发式扫描，非人工审查，仅供参考）。*")
    return "\n".join(lines)


def main() -> int:
    # 确保 stdout 以 UTF-8 输出（避免 Windows 控制台编码乱码）
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="Claude Code PR reviewer (structured Markdown output)")
    parser.add_argument("--pr", required=True, help="GitHub PR URL, e.g. https://github.com/owner/repo/pull/123")
    args = parser.parse_args()

    try:
        owner, repo, pull_number = parse_pr_url(args.pr)
        pr = fetch_pr(owner, repo, pull_number)
        files = fetch_pr_files(owner, repo, pull_number)
        review = build_review(pr, files)
        print(review)
        return 0
    except Exception as exc:
        print(f"[claude-review] 错误: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
