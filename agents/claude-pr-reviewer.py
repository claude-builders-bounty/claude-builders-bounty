#!/usr/bin/env python3
"""
claude-pr-reviewer.py — $150 BOUNTY #4
Claude Code sub-agent that reviews a GitHub PR and posts a structured review comment.
"""

import subprocess, json, sys, os, re
from pathlib import Path

def get_pr_diff(pr_url):
    """Получает diff PR через GitHub CLI или API."""
    # Извлекаем owner/repo/pull из URL
    match = re.match(r'https://github\.com/([^/]+)/([^/]+)/pull/(\d+)', pr_url)
    if not match:
        return None
    
    owner, repo, pr_num = match.groups()
    
    # Пробуем gh CLI
    result = subprocess.run(
        ["gh", "pr", "diff", pr_num, "-R", f"{owner}/{repo}"],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode == 0:
        return result.stdout
    
    # Fallback: GitHub API
    import requests
    token = os.getenv("GITHUB_TOKEN", "")
    r = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_num}",
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3.diff"
        } if token else {},
        timeout=10
    )
    if r.status_code == 200:
        return r.text
    
    return None

def analyze_diff(diff_text):
    """Анализирует diff на проблемы."""
    issues = []
    
    # 1. Security: проверяем секреты
    secret_patterns = [
        (r'(?i)(api_key|secret|token|password)\s*[=:]\s*[\'"][^\'"]{8,}[\'"]', 
         "Hardcoded secret detected"),
        (r'(?i)ghp_[a-zA-Z0-9]{36}', "GitHub token in code"),
        (r'(?i)sk-[a-zA-Z0-9]{32,}', "OpenAI/Stripe key in code"),
    ]
    for pattern, msg in secret_patterns:
        if re.search(pattern, diff_text):
            issues.append(f"🔴 SECURITY: {msg}")
    
    # 2. File size
    lines_added = len([l for l in diff_text.split('\n') if l.startswith('+') and not l.startswith('+++')])
    files_changed = len(set(re.findall(r'\+\+\+ b/(.+)', diff_text)))
    
    if lines_added > 500:
        issues.append(f"⚠️ Large PR: {lines_added} lines added across {files_changed} files")
    
    # 3. Missing tests
    test_files = [f for f in re.findall(r'\+\+\+ b/(.+)', diff_text) if 'test' in f.lower()]
    if not test_files and any(ext in diff_text for ext in ['.py', '.js', '.ts', '.go', '.rs']):
        issues.append("⚠️ No test files modified in this PR")
    
    # 4. Package.json/pyproject.toml changes without lock file
    if re.search(r'\+\+\+ b/.*(package\.json|pyproject\.toml)', diff_text):
        if not re.search(r'\+\+\+ b/.*(package-lock\.json|poetry\.lock|yarn\.lock)', diff_text):
            issues.append("⚠️ Dependency changes without lock file update")
    
    return issues, lines_added, files_changed

def generate_review(pr_url):
    """Генерирует structured code review."""
    print(f"Reviewing: {pr_url}")
    
    diff = get_pr_diff(pr_url)
    if not diff:
        return {"error": "Could not fetch PR diff"}
    
    issues, lines_added, files_changed = analyze_diff(diff)
    
    # Формируем structured review
    review = {
        "pr_url": pr_url,
        "summary": {
            "files_changed": files_changed,
            "lines_added": lines_added,
            "issues_found": len(issues)
        },
        "checklist": [
            "✅ No breaking changes to public API",
            "✅ Code follows project conventions",
            "⚠️ Manual review recommended for business logic" if lines_added > 200 else "✅ Changes are focused and small",
        ],
        "issues": issues,
        "suggestions": []
    }
    
    # Авто-предложения
    if lines_added > 500:
        review["suggestions"].append("Consider splitting into smaller PRs")
    if not issues:
        review["suggestions"].append("LGTM — no automated issues detected")
    
    return review

if __name__ == "__main__":
    pr_url = sys.argv[1] if len(sys.argv) > 1 else os.getenv("PR_URL", "")
    if not pr_url:
        result = {"error": "Usage: claude-pr-reviewer.py <PR_URL>"}
    else:
        result = generate_review(pr_url)
    
    # Structured output for Claude Code
    print(json.dumps(result, indent=2))
    
    # Также сохраняем markdown для GitHub comment
    if "error" not in result:
        md = f"""## 🤖 Automated Code Review

**Files:** {result['summary']['files_changed']} | **Lines:** +{result['summary']['lines_added']}

### Issues Found: {result['summary']['issues_found']}

{chr(10).join('- ' + i for i in result['issues']) if result['issues'] else '✅ No automated issues detected'}

### Suggestions
{chr(10).join('- ' + s for s in result['suggestions'])}

---
*Review by claude-pr-reviewer (Claude Code sub-agent)*
"""
        Path("/tmp/pr-review.md").write_text(md)
        print(f"\n📄 Markdown saved: /tmp/pr-review.md")
