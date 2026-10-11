import json
import os
import re
import urllib.error
import urllib.request
from urllib.parse import urlsplit

MAX_BYTES = 8 * 1024 * 1024


def parse_pr_url(url):
    parts = urlsplit(url)
    match = re.fullmatch(r'/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/pull/([1-9][0-9]*)/?', parts.path)
    if parts.scheme != 'https' or parts.netloc != 'github.com' or not match or parts.query or parts.fragment:
        raise ValueError('Expected https://github.com/owner/repo/pull/123')
    owner, repo, number = match.groups()
    if owner in {'.', '..'} or repo in {'.', '..'}:
        raise ValueError('Invalid repository')
    return owner, repo, int(number)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('Unexpected GitHub API redirect; use the canonical repository URL')


def get_json(url):
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'claude-review', 'X-GitHub-Api-Version': '2022-11-28'}
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        headers['Authorization'] = 'Bearer ' + token
    try:
        with urllib.request.build_opener(NoRedirect()).open(urllib.request.Request(url, headers=headers), timeout=30) as response:
            raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError('GitHub response exceeds 8 MiB; review a smaller PR')
        return json.loads(raw)
    except urllib.error.HTTPError as exc:
        hint = 'check access/token and API rate limits' if exc.code in (401, 403, 429) else 'check the public PR URL'
        raise ValueError(f'GitHub HTTP {exc.code}: {hint}') from None
    except urllib.error.URLError:
        raise ValueError('Cannot reach GitHub API; check network access or use --snapshot') from None


def fetch_pr(url):
    owner, repo, number = parse_pr_url(url)
    api = f'https://api.github.com/repos/{owner}/{repo}/pulls/{number}'
    meta = get_json(api)
    files = []
    for page in range(1, 31):
        batch = get_json(f'{api}/files?per_page=100&page={page}')
        files.extend(batch)
        if len(batch) < 100:
            break
    after = get_json(api)
    if (meta['head']['sha'], meta['base']['sha']) != (after['head']['sha'], after['base']['sha']):
        raise ValueError('PR changed while fetching; rerun for a consistent snapshot')
    return {'pr_url': url, 'title': meta['title'], 'head_sha': meta['head']['sha'], 'base_sha': meta['base']['sha'],
            'changed_files': meta['changed_files'], 'additions': meta['additions'], 'deletions': meta['deletions'],
            'files': files, 'source': 'GitHub public REST API /pulls and paginated /files'}
