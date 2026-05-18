#!/usr/bin/env python3
"""
claude-review — Static PR Reviewer with Structured Markdown Output
Fetches a GitHub PR diff, runs static analysis, outputs structured review.
No API key needed. Works on any public repo.

Usage:
    python claude-review.py https://github.com/owner/repo/pull/123
    python claude-review.py --output review.md https://github.com/owner/repo/pull/123
"""
import sys, re, json, urllib.request, textwrap, os

def fetch_pr_diff(pr_url):
    # Convert PR URL to diff URL
    m = re.match(r'https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)', pr_url)
    if not m:
        raise ValueError(f"Invalid PR URL: {pr_url}")
    owner, repo, num = m.groups()
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{num}"
    diff_url = f"https://github.com/{owner}/{repo}/pull/{num}.diff"
    
    # Fetch PR metadata
    req = urllib.request.Request(api_url, headers={
        'User-Agent': 'claude-review/1.0',
        'Accept': 'application/vnd.github.v3+json'
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        meta = json.loads(resp.read().decode())
    
    # Fetch diff
    req2 = urllib.request.Request(diff_url, headers={'User-Agent': 'claude-review/1.0'})
    with urllib.request.urlopen(req2, timeout=15) as resp:
        diff = resp.read().decode()
    
    return meta, diff, owner, repo, num

def analyze_diff(meta, diff):
    files = re.split(r'^diff --git ', diff, flags=re.MULTILINE)[1:]
    
    file_count = len(files)
    additions = diff.count('\n+') - diff.count('\n+++')
    deletions = diff.count('\n-') - diff.count('\n---')
    
    risks = []
    suggestions = []
    
    # Risk patterns — only match on NEW lines (+ ) or context lines, not removed
    diff_new_lines = '\n'.join(line for line in diff.split('\n') if line.startswith('+') and not line.startswith('+++'))
    
    if 'console.log' in diff_new_lines or 'print(' in diff_new_lines or 'logger.debug' in diff_new_lines:
        risks.append("Debug logging left in production code")
    if re.search(r'password|secret|api_key|private_key|token', diff_new_lines, re.I):
        risks.append("Potential secrets/credentials in diff — verify no hardcoded keys")
    if 'TODO' in diff_new_lines or 'FIXME' in diff_new_lines or 'HACK' in diff_new_lines:
        risks.append("Unresolved TODO/FIXME comments present")
    if re.search(r'eval\(|exec\(|Function\(|new Function', diff_new_lines):
        risks.append("Dynamic code execution detected — high risk")
    if 'innerHTML' in diff_new_lines or 'dangerouslySetInnerHTML' in diff_new_lines:
        risks.append("Potential XSS via innerHTML injection")
    if 'require(' in diff_new_lines and re.search(r'http://|ftp://', diff_new_lines):
        risks.append("Insecure protocol (http/ftp) in dependencies")
    if re.search(r'\bSELECT\b.*\bFROM\b.*\+', diff_new_lines, re.I):
        risks.append("Possible SQL injection via string concatenation")
    if 'process.exit(' in diff_new_lines:
        risks.append("process.exit() can crash the whole process")
    if additions > 500 and deletions < 50:
        risks.append("Large addition with minimal deletion — review for scope creep")
    if file_count > 15:
        risks.append("Large PR (>15 files) — consider splitting")
    
    # Suggestions — same logic, only on new lines
    if not re.search(r'test|spec|\.test\.', diff_new_lines, re.I) and additions > 50:
        suggestions.append("Add tests for new functionality")
    if additions > 100 and not re.search(r'README|CHANGELOG|\.md', diff_new_lines):
        suggestions.append("Update README/docs if user-facing changes")
    if re.search(r'function\s+\w+\s*\([^)]{60,}\)', diff_new_lines):
        suggestions.append("Consider destructuring long parameter lists")
    if additions > 0 and not re.search(r'try|catch|error', diff_new_lines, re.I):
        suggestions.append("Add error handling for new code paths")
    if file_count > 1 and not re.search(r'\.github|workflows|\.yml|\.yaml', diff_new_lines):
        suggestions.append("Consider if CI/CD updates are needed")
    
    # Confidence
    if len(risks) >= 3:
        confidence = "Low"
    elif len(risks) >= 1:
        confidence = "Medium"
    else:
        confidence = "High"
    
    return {
        "title": meta.get("title", "Unknown"),
        "author": meta.get("user", {}).get("login", "unknown"),
        "additions": additions,
        "deletions": deletions,
        "files": file_count,
        "risks": risks if risks else ["No major risks identified by static analysis"],
        "suggestions": suggestions if suggestions else ["Consider adding inline comments for complex logic"],
        "confidence": confidence,
        "pr_url": meta.get("html_url", ""),
        "description": meta.get("body", "")[:300].replace('\n', ' ')
    }

def format_review(data):
    lines = [
        f"# PR Review: {data['title']}",
        "",
        f"**Author:** @{data['author']}  ",
        f"**PR:** {data['pr_url']}  ",
        f"**Size:** +{data['additions']}/-{data['deletions']} in {data['files']} files  ",
        f"**Confidence:** {data['confidence']} 🔍",
        "",
        "## Summary",
        f"This PR by @{data['author']} modifies {data['files']} files with a net change of +{data['additions']}/-{data['deletions']}. "
        f"{data['description']}",
        "",
        "## Identified Risks",
    ]
    for r in data['risks']:
        lines.append(f"- ⚠️ {r}")
    lines += ["", "## Improvement Suggestions"]
    for s in data['suggestions']:
        lines.append(f"- 💡 {s}")
    lines += ["", "---", "*Generated by claude-review v1.0*"]
    return "\n".join(lines)

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print(__doc__)
        sys.exit(0)
    
    output_file = None
    pr_url = sys.argv[-1]
    if '--output' in sys.argv:
        idx = sys.argv.index('--output')
        output_file = sys.argv[idx + 1]
    
    try:
        meta, diff, owner, repo, num = fetch_pr_diff(pr_url)
        data = analyze_diff(meta, diff)
        review = format_review(data)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(review)
            print(f"Review written to {output_file}")
        else:
            print(review)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
