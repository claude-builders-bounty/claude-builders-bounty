#!/usr/bin/env python3
"""
claude-review — 为 PR 生成结构化 Markdown 审查
用法:
  python claude-review.py --pr <PR_URL>                  # 静态风险扫描
  python claude-review.py --pr <PR_URL> --claude         # 若有 claude CLI,生成深度 AI 审查
  python claude-review.py --diff <path/to/file.diff>     # 本地 diff 文件
输出: 结构化 Markdown (Summary / Risks / Suggestions / Confidence)
"""
import argparse, sys, os, re, textwrap, subprocess, json
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

RISK_PATTERNS = [
    (re.compile(r'(?i)(password|secret|api[_-]?key|token|credential|AWS_SECRET)\s*[:=]\s*["\'][^"\']{8,}'), "Hardcoded secret/credential detected"),
    (re.compile(r'(?i)(dotenv|\.env\.local|process\.env\.SNOWPACK_).*=\s*["\'][^"\']+["\']'), "Environment variable value hardcoded in source"),
    (re.compile(r'(?i)(exec|eval|spawn|child_process)\s*\('), "Dynamic code execution / subprocess call — review for injection"),
    (re.compile(r'(?i)(catch\s*\(.*\)\s*\{\s*\})'), "Empty catch block — swallowed exception"),
    (re.compile(r'(?i)print\s*\(.*password|\.log\(.*secret'), "Sensitive data logged to stdout"),
    (re.compile(r'(?i)(CREATE\s+TABLE|ALTER\s+TABLE|DROP\s+TABLE)'), "Raw DDL — confirm migration ownership"),
    (re.compile(r'(?i)(sudo\s|chmod\s777|chown\s)'), "Privilege escalation pattern"),
    (re.compile(r'(?i)(rm\s+-rf|rimraf\(|os\.remove)'), "Bulk destructive file operation"),
    (re.compile(r'(?i)(debugger;|console\.\w\(|print\()'), "Debug statement left in code"),
    (re.compile(r'(?i)(TODO|FIXME|HACK|XXX)\b'), "Unfinished marker left in code"),
    (re.compile(r'(?i)(http://(?!127\.|localhost))'), "Non-HTTPS URL in code (security risk)"),
    (re.compile(r'(?i)(\bany\b|as any)'), "TypeScript any — type safety reduced"),
    (re.compile(r'(?i)REPLACE INTO|INSERT OR IGNORE'), "Silent data overwrite — verify intent"),
]

TEST_PATTERNS = [
    re.compile(r'(?i)(describe|it|test|spec)\s*\('),
    re.compile(r'(?i)_test\.(py|js|ts)|test_.*\.(py|js|ts)'),
    re.compile(r'(?i)expect\s*\('),
]

BUG_PATTERNS = [
    (re.compile(r'(?i)(===|!==)\s*["\']'), "Loose equality on string — likely unintended"),
    (re.compile(r'(?i)\bnew Date\(\)'), "Server-side clock dependency — use ISO or injected clock"),
    (re.compile(r'(?i)\.then\(\(.*\)\s*=>\s*\{[^}]*catch'), "Misplaced .catch after .then block (swallows errors)"),
]

def fetch_diff_from_url(pr_url: str) -> str:
    pr_url = pr_url.rstrip('/')
    for suffix in ('.diff', '/diff'):
        url = pr_url if pr_url.endswith('.diff') else pr_url + suffix
        try:
            req = Request(url, headers={'User-Agent': 'claude-review/1.0'})
            with urlopen(req, timeout=15) as resp:
                return resp.read().decode('utf-8', errors='replace')
        except HTTPError:
            continue
        except URLError:
            continue
    raise RuntimeError(f"Failed to fetch diff from {pr_url}")

def fetch_pr_meta(pr_url: str) -> dict:
    api = pr_url.replace('https://github.com/', 'https://api.github.com/repos/').rstrip('/')
    if '/pull/' in api:
        api = api.replace('/pulls/', '/pulls/')
    else:
        # /owner/repo/pull/123 → /repos/owner/repo/pulls/123
        parts = pr_url.replace('https://github.com/', '').split('/')
        if len(parts) >= 4:
            api = f"https://api.github.com/repos/{parts[0]}/{parts[1]}/pulls/{parts[3]}"
    try:
        req = Request(api, headers={'User-Agent': 'claude-review/1.0'})
        with urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception:
        return {}

def parse_diff_stats(diff_text: str) -> dict:
    files_changed = set()
    added = 0
    removed = 0
    for line in diff_text.splitlines():
        if line.startswith('diff --git'):
            parts = line.split(' b/', 1)
            if len(parts) == 2:
                files_changed.add(parts[1])
        elif line.startswith('+') and not line.startswith('+++'):
            added += 1
        elif line.startswith('-') and not line.startswith('---'):
            removed += 1
    return {'files': files_changed, 'added': added, 'removed': removed, 'total_changed': added + removed}

def scan_risks(diff_text: str) -> list[str]:
    risks = []
    for pattern, msg in RISK_PATTERNS:
        for line in diff_text.splitlines():
            if line.startswith('+') and not line.startswith('+++'):
                if pattern.search(line):
                    risks.append(f"⚠ {msg}: `{line.strip()[:120]}`")
    return list(dict.fromkeys(risks))[:20]

def scan_suggestions(diff_text: str, stats: dict) -> list[str]:
    suggestions = []
    file_types = {}
    for f in stats['files']:
        ext = os.path.splitext(f)[1].lower()
        file_types[ext] = file_types.get(ext, 0) + 1

    has_test = any('test' in f.lower() or 'spec' in f.lower() for f in stats['files'])
    has_source_code = bool(set(file_types.keys()) & {'.py', '.js', '.ts', '.tsx', '.jsx', '.go', '.rs', '.java'})
    if has_source_code and not has_test:
        suggestions.append("No test files modified — consider adding unit/integration tests for changed logic.")

    added_lines = [l[1:] for l in diff_text.splitlines() if l.startswith('+') and not l.startswith('+++')]
    total_added = len(added_lines) or 1
    test_lines = sum(1 for l in added_lines if any(p.search(l) for p in TEST_PATTERNS))
    if test_lines / total_added < 0.1 and has_source_code:
        suggestions.append(f"Test coverage low: {test_lines}/{total_added} added lines are test-related (target >20%).")

    if stats['total_changed'] > 500:
        suggestions.append(f"Large PR ({stats['total_changed']} changed lines) — consider splitting into smaller, reviewable chunks.")

    long_funcs = []
    current_len = 0
    for line in added_lines:
        stripped = line.strip()
        if stripped and not stripped.startswith(('import', 'from', '#', '//', '/*', '*', '"""')):
            current_len += 1
            if current_len > 80:
                long_funcs.append(stripped[:60])
                current_len = 0
        else:
            current_len = 0
    if long_funcs:
        suggestions.append(f"Found added blocks >80 lines without break — consider extracting smaller functions.")

    for pattern, msg in BUG_PATTERNS:
        for line in added_lines:
            if pattern.search(line):
                suggestions.append(f"Potential bug: {msg}: `{line.strip()[:100]}`")

    return list(dict.fromkeys(suggestions))[:10]

def classify_risk_level(risks: list[str], stats: dict) -> str:
    high_keywords = ['secret', 'credential', 'rm -rf', 'sudo', 'DROP TABLE', 'exec(', 'eval(']
    high_hits = sum(1 for r in risks if any(k.lower() in r.lower() for k in high_keywords))
    if high_hits >= 2 or stats['total_changed'] > 1000:
        return "High"
    if high_hits == 1 or len(risks) >= 4 or stats['total_changed'] > 300:
        return "Medium"
    return "Low"

def build_summary(pr_url: str, meta: dict, stats: dict, risks: list, suggestions: list, risk_level: str) -> str:
    title = meta.get('title', pr_url.split('/')[-1])
    author = meta.get('user', {}).get('login', 'unknown')
    state = meta.get('state', 'unknown')
    base = meta.get('base', {}).get('ref', '')
    head = meta.get('head', {}).get('ref', '')
    mergeable = meta.get('mergeable_state', 'unknown')
    commits = meta.get('commits', 0)
    files = meta.get('changed_files', len(stats['files']))

    file_list = ', '.join(sorted(stats['files'])[:10])
    if len(stats['files']) > 10:
        file_list += f" (+{len(stats['files'])-10} more)"

    section = f"""## Summary

- **PR:** [{title}]({pr_url}) by @{author} ({state})
- **Branch:** `{head}` → `{base}` | mergeable: {mergeable} | commits: {commits} | files: {files}
- **Diff stats:** +{stats['added']}/-{stats['removed']} lines across {len(stats['files'])} files
- **Key files:** {file_list}
- **Confidence:** {risk_level}
"""
    if risks:
        section += "\n## Identified Risks\n\n"
        section += '\n'.join(risks) + "\n"
    else:
        section += "\n## Identified Risks\n\nNo high-risk patterns detected.\n"

    if suggestions:
        section += "\n## Improvement Suggestions\n\n"
        section += '\n'.join(suggestions) + "\n"
    else:
        section += "\n## Improvement Suggestions\n\nLooking good — no major suggestions.\n"

    return section

def run_claude_review(diff: str, meta: dict) -> str | None:
    if not shutil.which('claude'):
        return None
    prompt = f"""You are a senior code reviewer. Analyze this PR diff and produce a structured Markdown review with these exact sections:

## Summary
2-3 sentence summary of what this PR does.

## Identified Risks
Bullet list of specific risks (security, data loss, regression, scalability). Only real risks.

## Improvement Suggestions
Bullet list of actionable, specific suggestions (not generic advice).

## Confidence
One of: Low / Medium / High — how confident you are this review is complete given the diff size.

PR title: {meta.get('title', 'N/A')}
Diff:
{diff[:8000]}
"""
    try:
        import shutil
        result = subprocess.run(['claude', '-p', prompt], capture_output=True, text=True, timeout=120)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass
    return None

def main():
    parser = argparse.ArgumentParser(description='claude-review: PR review generator')
    parser.add_argument('--pr', help='GitHub PR URL (https://github.com/owner/repo/pull/123)')
    parser.add_argument('--diff', help='Local diff file path')
    parser.add_argument('--claude', action='store_true', help='Use claude CLI for AI review (if available)')
    parser.add_argument('-o', '--output', help='Output file (default: stdout)')
    args = parser.parse_args()

    if args.pr:
        diff_text = fetch_diff_from_url(args.pr)
        meta = fetch_pr_meta(args.pr)
    elif args.diff:
        diff_text = open(args.diff, encoding='utf-8').read()
        meta = {}
    else:
        parser.error('Provide --pr <url> or --diff <file>')
        sys.exit(1)

    ai_review = None
    if args.claude:
        ai_review = run_claude_review(diff_text, meta)

    if ai_review:
        output = ai_review
    else:
        stats = parse_diff_stats(diff_text)
        risks = scan_risks(diff_text)
        suggestions = scan_suggestions(diff_text, stats)
        risk_level = classify_risk_level(risks, stats)
        output = build_summary(args.pr or 'local', meta, stats, risks, suggestions, risk_level)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f'→ {args.output} ({len(output)} chars)')
    else:
        print(output)

if __name__ == '__main__':
    import shutil
    main()