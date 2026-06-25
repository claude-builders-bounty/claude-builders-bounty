#!/usr/bin/env python3
"""
claude-review - PR审查子代理
用法: python claude-review.py --pr https://github.com/owner/repo/pull/123
或者作为GitHub Action运行
"""

import argparse, json, os, subprocess, sys, urllib.request, re
from typing import Optional

def get_pr_diff(pr_url: str) -> Optional[str]:
    """获取PR的diff"""
    api_url = pr_url.replace("github.com", "api.github.com/repos") + "/files"
    req = urllib.request.Request(api_url, headers={
        "Authorization": "token " + os.getenv("GITHUB_TOKEN", ""),
        "Accept": "application/vnd.github.v3+json"
    })
    try:
        r = urllib.request.urlopen(req, timeout=30)
        files = json.loads(r.read().decode())
        diff = ""
        for f in files:
            diff += "File: %s (%s)\n" % (f["filename"], f["status"])
            if f.get("patch"):
                diff += f["patch"][:500] + "\n\n"
        return diff
    except Exception as e:
        return "Error fetching PR: %s" % e

def analyze_diff(diff: str) -> dict:
    """分析diff生成审查意见"""
    issues = []
    patterns = [
        (r"(?i)(password|secret|key|token|credential)\s*=\s*['\"][^'\"]+['\"]", "硬编码密钥"),
        (r"print\(|console\.log\(", "调试代码残留"),
        (r"(?i)except\s*(Exception)?\s*:\s*pass", "静默捕获异常"),
        (r"(?i)SELECT\s+\*\s+FROM", "SELECT * 建议指定列名"),
        (r"(?i)(TODO|FIXME|HACK|XXX)", "待办事项残留"),
        (r"(?i)exec\s*\(|eval\s*\(", "危险函数调用"),
        (r"(?i)(api_key|secret|private_key)\s*=", "敏感信息泄露风险"),
        (r"(?i)(\d{4}.*\d{4}.*\d{4}.*\d{4})", "可能的信用卡号"),
        (r"(?i)drop\s+table|truncate\s+", "危险SQL操作"),
    ]
    
    for pattern, desc in patterns:
        matches = re.findall(pattern, diff)
        if matches:
            issues.append({"severity": "medium" if "危险" in desc else "low",
                          "description": desc, "count": len(matches)})
    
    # 代码统计
    lines_added = len(re.findall(r'^\+', diff, re.MULTILINE))
    lines_removed = len(re.findall(r'^-', diff, re.MULTILINE))
    files_changed = len(re.findall(r'^File:', diff, re.MULTILINE))
    
    return {
        "summary": {
            "files_changed": files_changed,
            "lines_added": lines_added,
            "lines_removed": lines_removed,
        },
        "issues": issues[:5],
        "score": max(0, 10 - len(issues))
    }

def main():
    parser = argparse.ArgumentParser(description="PR Review Agent")
    parser.add_argument("--pr", required=True, help="PR URL")
    parser.add_argument("--github-token", help="GitHub Token")
    args = parser.parse_args()
    
    if args.github_token:
        os.environ["GITHUB_TOKEN"] = args.github_token
    
    diff = get_pr_diff(args.pr)
    result = analyze_diff(diff)
    
    # 生成Markdown报告
    report = """## PR Review Report

### Summary
- Files Changed: %(files)d
- Lines Added: %(added)d
- Lines Removed: %(removed)d
- Quality Score: %(score)d/10

""" % {"files": result["summary"]["files_changed"],
       "added": result["summary"]["lines_added"],
       "removed": result["summary"]["lines_removed"],
       "score": result["score"]}
    
    if result["issues"]:
        report += "### Issues Found\n\n"
        for issue in result["issues"]:
            report += "- [%s] %s (%d occurrences)\n" % (
                issue["severity"], issue["description"], issue["count"])
    
    if not result["issues"]:
        report += "### No issues found. LGTM! 👍\n"
    
    print(report)

if __name__ == "__main__":
    main()
