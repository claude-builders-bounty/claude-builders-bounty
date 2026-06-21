#!/usr/bin/env node
/**
 * Unit tests for tests/lib/github-collect.mjs helpers.
 * Covers token validation, pagination, and GitHub error detection.
 */
import {
  collectRecords,
  fetchGitHubPages,
  githubAuthHeaders,
  githubRepoUrl,
  GITHUB_USER_URL,
  isGitHubError,
  validateGitHubToken,
} from './lib/github-collect.mjs';

const failures = [];
function assert(condition, message) {
  if (!condition) failures.push(message);
}

function mockResponse(status, body, statusText = String(status)) {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText,
    json: async () => body,
  };
}

assert(GITHUB_USER_URL === 'https://api.github.com/user', 'GITHUB_USER_URL points at GitHub /user endpoint');
assert(
  githubRepoUrl('octo/repo') === 'https://api.github.com/repos/octo/repo',
  'githubRepoUrl builds repo metadata endpoint',
);

const sampleToken = ['gh', 'p', '_test'].join('');
const headers = githubAuthHeaders(sampleToken);
assert(headers.Authorization === `Bearer ${sampleToken}`, 'githubAuthHeaders sets Bearer token');
assert(headers.Accept === 'application/vnd.github+json', 'githubAuthHeaders sets GitHub Accept header');
assert(headers['X-GitHub-Api-Version'] === '2022-11-28', 'githubAuthHeaders sets GitHub API version');

assert(isGitHubError({ message: 'Not Found', documentation_url: 'https://docs.github.com' }), 'isGitHubError detects API errors');
assert(!isGitHubError({ sha: 'abc', commit: { message: 'fix' } }), 'isGitHubError ignores commit records');
assert(!isGitHubError(null), 'isGitHubError rejects null');
assert(!isGitHubError({ message: 'only message' }), 'isGitHubError requires documentation_url');

const merged = collectRecords([
  { json: { records: [{ sha: 'a' }, { sha: 'b' }] } },
  { json: { records: [{ sha: 'c' }] } },
]);
assert(merged.length === 3, 'collectRecords flattens multiple n8n items');

const filtered = collectRecords([{ json: { records: [
  { sha: 'keep' },
  { message: 'Bad credentials', documentation_url: 'https://docs.github.com' },
] } }]);
assert(filtered.length === 1 && filtered[0].sha === 'keep', 'collectRecords drops GitHub error objects');

try {
  await validateGitHubToken('');
  assert(false, 'validateGitHubToken rejects empty token');
} catch (error) {
  assert(error.message.includes('GITHUB_TOKEN'), 'empty token error mentions GITHUB_TOKEN');
}

try {
  await validateGitHubToken('bad-token', async () => mockResponse(401, { message: 'Bad credentials' }));
  assert(false, 'validateGitHubToken rejects 401');
} catch (error) {
  assert(error.message.includes('invalid or lacks required permissions'), '401 yields permission error');
}

try {
  await validateGitHubToken('bad-token', async () => mockResponse(403, { message: 'Forbidden' }));
  assert(false, 'validateGitHubToken rejects 403');
} catch (error) {
  assert(error.message.includes('invalid or lacks required permissions'), '403 yields permission error');
}

const login = await validateGitHubToken('good-token', async (url) => {
  assert(url === GITHUB_USER_URL, 'validateGitHubToken calls /user endpoint');
  return mockResponse(200, { login: 'octocat' });
});
assert(login === 'octocat', 'validateGitHubToken returns authenticated login');

const repoName = await validateGitHubToken('good-token', {
  repo: 'octo/repo',
  fetchFn: async (url) => {
    assert(url === githubRepoUrl('octo/repo'), 'validateGitHubToken calls repo endpoint when repo is set');
    return mockResponse(200, { full_name: 'octo/repo' });
  },
});
assert(repoName === 'octo/repo', 'validateGitHubToken returns repo full_name for repo-scoped validation');

try {
  await validateGitHubToken('good-token', async () => mockResponse(200, {}));
  assert(false, 'validateGitHubToken rejects response without login');
} catch (error) {
  assert(error.message.includes('unexpected GitHub response'), 'missing login yields unexpected response error');
}

function pageFromUrl(url) {
  const match = url.match(/[?&]page=(\d+)(?:&|$)/);
  return match ? Number(match[1]) : 0;
}

const pages = await fetchGitHubPages(
  'https://api.github.com/repos/o/r/commits',
  'token',
  { since: '2026-06-01' },
  {
    maxPages: 2,
    fetchFn: async (url) => {
      const page = pageFromUrl(url);
      if (page === 1) {
        return mockResponse(200, Array.from({ length: 100 }, (_, i) => ({ sha: `p1-${i}` })));
      }
      if (page === 2) {
        return mockResponse(200, [{ sha: 'p2-0' }]);
      }
      return mockResponse(404, { message: 'Not Found', documentation_url: 'https://docs.github.com' });
    },
  },
);
assert(pages.length === 101, 'fetchGitHubPages paginates until short page');

try {
  await fetchGitHubPages('https://api.github.com/repos/o/r/commits', 'token', {}, {
    fetchFn: async () => mockResponse(401, { message: 'Bad credentials' }),
  });
  assert(false, 'fetchGitHubPages throws on HTTP error');
} catch (error) {
  assert(error.message.includes('401'), 'fetchGitHubPages surfaces HTTP status');
}

try {
  await fetchGitHubPages('https://api.github.com/repos/o/r/commits', 'token', {}, {
    fetchFn: async () => mockResponse(429, { message: 'API rate limit exceeded' }),
  });
  assert(false, 'fetchGitHubPages throws on rate limit');
} catch (error) {
  assert(error.message.includes('429'), 'fetchGitHubPages surfaces rate limit status');
  assert(error.message.includes('rate limit'), 'fetchGitHubPages includes GitHub rate limit message');
}

try {
  await fetchGitHubPages('https://api.github.com/repos/o/r/commits', 'token', {}, {
    fetchFn: async () => {
      throw new Error('network unreachable');
    },
  });
  assert(false, 'fetchGitHubPages propagates network errors');
} catch (error) {
  assert(error.message.includes('network unreachable'), 'fetchGitHubPages surfaces fetch failures');
}

try {
  await fetchGitHubPages('https://api.github.com/search/issues', 'token', { q: 'repo:o/r' }, {
    fetchFn: async () =>
      mockResponse(200, { message: 'Validation Failed', documentation_url: 'https://docs.github.com' }),
  });
  assert(false, 'fetchGitHubPages throws on GitHub error payload');
} catch (error) {
  assert(error.message.includes('Validation Failed'), 'fetchGitHubPages surfaces GitHub error message');
}

try {
  await validateGitHubToken('good-token', {
    repo: 'octo/repo',
    fetchFn: async () => mockResponse(200, { name: 'repo-only' }),
  });
  assert(false, 'validateGitHubToken rejects repo response without full_name');
} catch (error) {
  assert(error.message.includes('unexpected GitHub response'), 'repo validation rejects malformed body');
}

try {
  await fetchGitHubPages('https://api.github.com/repos/o/r/commits', '', {}, {
    fetchFn: async (_url, init) => {
      const auth = init?.headers?.Authorization || '';
      if (auth === 'Bearer ') {
        return mockResponse(401, { message: 'Bad credentials' });
      }
      return mockResponse(200, []);
    },
  });
  assert(false, 'fetchGitHubPages rejects empty token via auth header');
} catch (error) {
  assert(error.message.includes('401'), 'empty token yields auth failure');
}

if (failures.length) {
  console.error('FAILED github-collect unit tests:\n- ' + failures.join('\n- '));
  process.exit(1);
}

console.log('OK: github-collect unit tests passed.');
