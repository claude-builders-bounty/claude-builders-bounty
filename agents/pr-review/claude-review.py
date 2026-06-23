#!/usr/bin/env python3
# CLI PR review agent
import argparse, urllib.request as u, json as j, os, re

github_token = os.environ.get('GITHUB_TOKEN', '')

def fetch(url):
    h = {'User-Agent': 'claude-review'}
    if github_token:
        h['Authorization'] = 'Bearer ' + github_token
    return j.loads(u.urlopen(u.Request(url, headers=h), timeout=30).read())

def review(url):
    api = url.replace('github.com', 'api.github.com/repos')
    pr = fetch(api)
    f = fetch(api + '/files')
    diff = u.urlopen(pr.get('diff_url', '')).read().decode()[:5000] if pr.get('diff_url') else ''
    s = 'Changes %d file(s): +%d/-%d.' % (len(f), pr.get('additions',0), pr.get('deletions',0))
    risks, sug = [], []
    if len(f) > 20: risks.append('Large PR')
    if re.search(r'secret|password|token=', diff, re.I): risks.append('Secret exposure (HIGH)')
    if not re.search(r'test|spec', diff, re.I): sug.append('Add tests')
    if re.search(r'TODO|FIXME', diff): risks.append('Unresolved TODOS')
    if not risks: risks.append('No obvious risks')
    conf = 'High' if 'HIGH' in str(risks) else 'Medium'
    out = ['## PR Review', s, '', '### Risks'] + ['- '+r for r in risks]
    out += ['', '### Suggestions'] + ['- '+x for x in sug] + ['', '**Confidence**: '+conf]
    return '\n'.join(out)

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--pr', required=True)
    print(review(p.parse_args().pr))
