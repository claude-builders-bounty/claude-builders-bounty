#!/usr/bin/env python3
import argparse, os, re, shutil, subprocess, sys, urllib.parse

def parse_pr(url):
    m=re.fullmatch(r'https://github\.com/([^/]+)/([^/]+)/pull/(\d+)',url.rstrip('/'))
    if not m: raise SystemExit('Expected https://github.com/owner/repo/pull/123')
    return m.groups()

def fetch_diff(url):
    owner,repo,num=parse_pr(url)
    cp=subprocess.run(['gh','pr','diff',num,'--repo',f'{owner}/{repo}'],capture_output=True,text=True,check=True,timeout=60)
    return cp.stdout

def fallback_review(diff):
    files=len(re.findall(r'^diff --git ',diff,re.M))
    lines=diff.splitlines()
    adds=sum(line.startswith('+') and not line.startswith('+++ ') for line in lines)
    dels=sum(line.startswith('-') and not line.startswith('--- ') for line in lines)
    risks=[]; suggestions=[]
    if re.search(r'password|secret|token|api[_-]?key',diff,re.I): risks.append('Diff contains credential-sensitive terms; verify no secret material is committed.')
    if re.search(r'\b(eval|exec)\s*\(',diff): risks.append('Dynamic execution appears in the diff; validate inputs and threat model.')
    if adds+dels>500: risks.append('Large change surface increases review risk; consider splitting or adding targeted tests.')
    if not re.search(r'test|spec',diff,re.I): suggestions.append('Add or confirm targeted regression coverage for the changed behavior.')
    if files>5: suggestions.append('Call out cross-file behavior changes in the PR description to make verification easier.')
    if not risks: risks=['No high-signal risk detected by the deterministic fallback; human/Claude review is still recommended.']
    if not suggestions: suggestions=['Keep the regression test focused on the reported behavior and edge cases.']
    conf='High' if files<=3 and adds+dels<=150 else 'Medium'
    return f'''## Summary
This PR changes {files} file(s) with approximately {adds} added and {dels} removed lines. The fallback reviewer summarizes only signals visible in the diff and does not infer unobserved runtime behavior.

## Risks
''' + ''.join(f'- {x}\n' for x in risks) + '\n## Improvement suggestions\n' + ''.join(f'- {x}\n' for x in suggestions) + f'\n## Confidence\n{conf}\n'

def valid_review(text):
    required = ['Summary', 'Risks', 'Improvement suggestions', 'Confidence']
    if not text:
        return False
    headings=list(re.finditer(r'^## (Summary|Risks|Improvement suggestions|Confidence)[ \t]*$',text,re.M))
    if [heading.group(1) for heading in headings] != required:
        return False
    sections=[text[heading.end():headings[index+1].start() if index+1<len(headings) else len(text)].strip()
              for index,heading in enumerate(headings)]
    if not all(sections):
        return False
    if any(not re.search(r'^\s*[-*+]\s+\S',section,re.M) for section in sections[1:3]):
        return False
    return sections[3] in {'Low','Medium','High'}

def review_with_claude(diff):
    binary=os.environ.get('CLAUDE_BIN','claude')
    if not shutil.which(binary): return None
    prompt=(
        'Review the following GitHub PR diff. Return only a Markdown review with '
        'these four headings in this order: ## Summary, ## Risks, '
        '## Improvement suggestions, ## Confidence. '
        'Summary must contain 2-3 sentences. Risks and Improvement suggestions '
        'must contain non-empty bullet lists. Confidence must contain only '
        'Low, Medium, or High. Do not claim runtime behavior that the diff does not establish.\n\n'
    )+diff
    try:
        cp=subprocess.run([binary,'-p',prompt],capture_output=True,text=True,timeout=120)
    except (OSError,subprocess.TimeoutExpired):
        return None
    if cp.returncode!=0: return None
    out=cp.stdout.strip()+'\n'
    return out if valid_review(out) else None

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--pr',required=True); ap.add_argument('--fallback-only',action='store_true'); a=ap.parse_args()
    try:
        diff=fetch_diff(a.pr)
    except (OSError,subprocess.CalledProcessError,subprocess.TimeoutExpired) as error:
        print(f'Unable to fetch PR diff: {error}',file=sys.stderr)
        return 1
    out=None if a.fallback_only else review_with_claude(diff)
    if not out: out=fallback_review(diff)
    print(out,end='')
    return 0
if __name__=='__main__': sys.exit(main())
