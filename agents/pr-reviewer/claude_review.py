#!/usr/bin/env python3
"""claude-review — 抓一个 GitHub PR 的 diff，出一份结构化的 Markdown 评审。

用法：
    claude-review --pr https://github.com/owner/repo/pull/123
    claude-review --pr owner/repo#123 --out review.md
    claude-review --diff path/to.diff --title "feat: x"      # 离线看本地 diff

设计上分两层：
  1. 确定性分析（永远跑）：从 diff 里量出规模、碰了哪些区域、有没有测试、
     有没有高危模式（迁移、鉴权、密钥、破坏性 SQL、依赖变动……）。
  2. 可选的模型润色：设置了 ANTHROPIC_API_KEY 或 OPENAI_API_KEY 时，
     把第 1 层的结论交给模型写成 2–3 句摘要；没有 key 就用确定性模板。

所以没有 API key 也能用，输出依然基于真实 diff —— 不是编的。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

# --------------------------------------------------------------------------
# 取 PR 数据
# --------------------------------------------------------------------------

PR_URL_RE = re.compile(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)")


def parse_pr(target: str) -> tuple[str, str, int]:
    m = PR_URL_RE.match(target)
    if m:
        return m.group(1), m.group(2), int(m.group(3))
    m = re.match(r"([^/\s#]+)/([^/\s#]+)#(\d+)", target)
    if m:
        return m.group(1), m.group(2), int(m.group(3))
    raise SystemExit(f"看不懂的 PR 地址：{target}")


def gh_get(url: str, accept: str = "application/vnd.github+json") -> tuple[int, bytes]:
    headers = {"User-Agent": "claude-review", "Accept": accept}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def fetch_pr(owner: str, repo: str, number: int) -> tuple[dict, str]:
    code, body = gh_get(f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}")
    if code != 200:
        raise SystemExit(f"拿不到 PR #{number}（HTTP {code}）：{body[:200]!r}")
    meta = json.loads(body)

    code, diff = gh_get(
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}",
        accept="application/vnd.github.v3.diff",
    )
    if code != 200:
        raise SystemExit(f"拿不到 diff（HTTP {code}）")
    return meta, diff.decode("utf-8", "replace")


# --------------------------------------------------------------------------
# 确定性分析
# --------------------------------------------------------------------------

# 每条风险 = (正则, 说明, 等级, 上下文正则)。上下文正则用来排除“只是提到”而非“真的执行”。
SQL_CTX = re.compile(r"(?i)(execute|executemany|prepare|cursor|psql|mysql|sqlite|db\.|raw|query)\s*[\(\.\"']")
EXEC_CTX = re.compile(r"(?i)(subprocess|popen|system|run|call|check_output|eval|exec)\s*[\(\.]")

RISK_PATTERNS = [
    (r"\bDROP\s+TABLE\b|\bTRUNCATE\b", "包含破坏性 SQL（DROP / TRUNCATE）", "high", SQL_CTX),
    (r"\bDELETE\s+FROM\b(?![\s\S]{0,200}?\bWHERE\b)", "`DELETE FROM` 可能缺少 `WHERE`", "high", SQL_CTX),
    (r"(?i)(api[_-]?key|secret|password)\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}", "疑似硬编码密钥", "high", None),
    (r"(?i)chmod\s+777|--no-verify", "包含可能绕过保护的操作", "medium", None),
    (r"(?i)subprocess\.|os\.system|eval\(|exec\(", "执行外部命令或动态求值", "medium", EXEC_CTX),
    (r"(?i)disable.*(csrf|xss|verify_ssl|ssl_verify)", "关闭安全校验", "high", None),
]

# 这些路径里的“危险字样”多半是测试夹具或文档示例，不算风险
NON_PROD_PATH = re.compile(r"(^|/)(tests?|__tests__|spec|samples?|fixtures?|docs?)/|\.(md|mdx|txt|rst)$", re.IGNORECASE)
# 正则/字符串定义里的字样，不是真的执行
REGEX_LIKE = re.compile(r"\\b|\\s|\[\^|\(\?|r\"|r'|\|[^\n]*\|")

TEST_HINTS = re.compile(r"(^|/)(tests?|__tests__|spec)/|(_test|\.test|_spec|\.spec)\.", re.IGNORECASE)


def analyze(diff: str, meta: dict | None = None) -> dict:
    files: list[dict] = []
    current = None
    added = removed = 0
    prod_lines: list[str] = []      # 只收“生产代码”里新增的行
    all_lines: list[str] = []       # 全量新增行，用于其它检查

    for line in diff.splitlines():
        if line.startswith("diff --git "):
            if current:
                files.append(current)
            name = line.split(" b/", 1)[-1]
            current = {"path": name, "added": 0, "removed": 0, "binary": False}
            continue
        if current is None:
            continue
        if line.startswith("+") and not line.startswith("+++"):
            current["added"] += 1
            added += 1
            body = line[1:]
            all_lines.append(body)
            if not NON_PROD_PATH.search(current["path"]) and not REGEX_LIKE.search(body):
                prod_lines.append(body)
        elif line.startswith("-") and not line.startswith("---"):
            current["removed"] += 1
            removed += 1
        elif line.startswith("Binary files"):
            current["binary"] = True
    if current:
        files.append(current)

    text = "\n".join(prod_lines)
    paths = " ".join(f["path"] for f in files)
    risks = []
    for pattern, label, level, ctx in RISK_PATTERNS:
        hit = False
        for line in prod_lines:
            if not re.search(pattern, line):
                continue
            if ctx is not None and not ctx.search(line):
                continue  # 只是“提到”这个词，不当作执行
            hit = True
            break
        if hit:
            risks.append({"label": label, "level": level})

    if re.search(r"(^|/)\.env($|\.)", paths):
        risks.append({"label": "改动涉及环境变量文件", "level": "high"})
    if re.search(r"(?i)migrations?/|schema\.sql", paths):
        risks.append({"label": "改动数据库结构", "level": "medium"})
    if re.search(r"package-lock\.json|yarn\.lock|pnpm-lock", paths):
        risks.append({"label": "锁文件变动（依赖升级/降级）", "level": "medium"})

    touched_tests = any(TEST_HINTS.search(f["path"]) for f in files)
    code_files = [f for f in files if re.search(r"\.(py|ts|tsx|js|jsx|go|rs|java|rb|sql|sh)$", f["path"])]
    if code_files and not touched_tests:
        risks.append({"label": "改了代码但没带测试", "level": "medium"})

    biggest = sorted(files, key=lambda f: f["added"], reverse=True)[:5]
    areas = sorted({f["path"].split("/")[0] for f in files})

    suggestions = []
    if not touched_tests and code_files:
        suggestions.append("补一条能复现本次行为的测试；没有测试的修复很难验证是否真的修好。")
    if any(r["label"].startswith("改动数据库结构") for r in risks):
        suggestions.append("迁移文件请保证可重复执行（`IF NOT EXISTS`），并在 PR 描述里写回滚方式。")
    if added > 800:
        suggestions.append(f"本次 +{added} 行，建议拆成多个 PR；大 diff 的评审质量会明显下降。")
    if any(f["binary"] for f in files):
        suggestions.append("包含二进制文件，确认是否真的需要进仓库（还是放对象存储）。")
    if not suggestions:
        suggestions.append("没有发现需要阻断的问题；保持改动聚焦即可。")

    high = [r for r in risks if r["level"] == "high"]
    if high:
        confidence = "Low"
    elif len(risks) >= 3 or added > 500:
        confidence = "Medium"
    else:
        confidence = "High"

    return {
        "files": files,
        "added": added,
        "removed": removed,
        "risks": risks,
        "suggestions": suggestions,
        "confidence": confidence,
        "areas": areas,
        "biggest": biggest,
        "touched_tests": touched_tests,
    }


# --------------------------------------------------------------------------
# 可选：模型润色摘要
# --------------------------------------------------------------------------

def summarize_with_model(prompt: str) -> str | None:
    """有 key 就调一次模型写摘要；失败返回 None，调用方退回模板。"""
    anthropic = os.environ.get("ANTHROPIC_API_KEY")
    openai = os.environ.get("OPENAI_API_KEY")
    payload_tpl = None
    url = None
    headers = {"Content-Type": "application/json"}

    if anthropic:
        url = "https://api.anthropic.com/v1/messages"
        headers["x-api-key"] = anthropic
        headers["anthropic-version"] = "2023-06-01"
        payload_tpl = ("anthropic", "claude-sonnet-4-5")
    elif openai:
        base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        url = base + "/chat/completions"
        headers["Authorization"] = f"Bearer {openai}"
        payload_tpl = ("openai", os.environ.get("OPENAI_MODEL", "gpt-4o-mini"))
    else:
        return None

    kind, model = payload_tpl
    if kind == "anthropic":
        body = {"model": model, "max_tokens": 300,
                "messages": [{"role": "user", "content": prompt}]}
    else:
        body = {"model": model, "max_tokens": 300,
                "messages": [{"role": "user", "content": prompt}]}

    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        return None

    if kind == "anthropic":
        blocks = data.get("content") or []
        return "".join(b.get("text", "") for b in blocks).strip() or None
    return (data.get("choices") or [{}])[0].get("message", {}).get("content", "").strip() or None


# --------------------------------------------------------------------------
# 出 Markdown
# --------------------------------------------------------------------------

def render(meta: dict | None, res: dict, use_model: bool) -> str:
    title = (meta or {}).get("title", "(本地 diff)")
    files = res["files"]
    if use_model:
        prompt = (
            "用 2-3 句话概括这个 PR 改了什么、最值得注意的一点是什么。"
            "只输出句子本身，不要标题、不要客套。\n\n"
            f"标题：{title}\n"
            f"文件：{', '.join(f['path'] for f in files[:12])}\n"
            f"增删：+{res['added']} / -{res['removed']}\n"
        )
        summary = summarize_with_model(prompt)
    else:
        summary = None

    if not summary:
        top = ", ".join(f"`{f['path']}`" for f in res["biggest"][:3]) or "（无文件）"
        summary = (
            f"这个 PR 改了 {len(files)} 个文件，+{res['added']} / -{res['removed']} 行，"
            f"主要集中在 {', '.join(res['areas'][:4]) or '根目录'}。"
            f"改动量最大的是 {top}。"
        )
        if res["touched_tests"]:
            summary += " 本次带上了测试改动。"
        else:
            summary += " 没有带测试改动。"

    lines = ["## 评审", "", f"**PR**：{title}", "", "### 改动概述", "", summary, ""]

    lines += ["### 风险", ""]
    if res["risks"]:
        for r in res["risks"]:
            lines.append(f"- **[{r['level']}]** {r['label']}")
    else:
        lines.append("- 没有检出声明的风险模式（不代表没有风险，只说明没命中已知模式）。")
    lines.append("")

    lines += ["### 改进建议", ""]
    for s in res["suggestions"]:
        lines.append(f"- {s}")
    lines.append("")

    lines += ["### 置信度", "", f"**{res['confidence']}**", ""]
    if res["confidence"] != "High":
        lines.append("> 置信度不高时会说明原因：命中了高危模式，或改动面过大，需要人再看一遍。")
        lines.append("")

    lines += ["---", "", "<sub>由 claude-review 生成：确定性分析来自真实 diff；摘要由模型润色（如配置了 key）。</sub>"]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="抓 GitHub PR 的 diff，输出结构化评审")
    ap.add_argument("--pr", help="PR 地址，如 https://github.com/owner/repo/pull/123")
    ap.add_argument("--diff", help="本地 diff 文件（与 --pr 二选一）")
    ap.add_argument("--title", default="", help="配合 --diff 使用的标题")
    ap.add_argument("--out", help="写入文件而不是打印")
    args = ap.parse_args()

    if not args.pr and not args.diff:
        ap.error("要么给 --pr，要么给 --diff")

    if args.pr:
        owner, repo, number = parse_pr(args.pr)
        meta, diff = fetch_pr(owner, repo, number)
    else:
        meta = {"title": args.title or "(本地 diff)"}
        diff = open(args.diff, encoding="utf-8", errors="replace").read()

    res = analyze(diff, meta)
    md = render(meta, res, use_model=True)

    if args.out:
        open(args.out, "w", encoding="utf-8").write(md + "\n")
        print(f"已写入 {args.out}")
    else:
        print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
