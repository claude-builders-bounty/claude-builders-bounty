import { fetchPrDiff } from '../src/github';

const mockGet = jest.fn();

jest.mock('@octokit/rest', () => ({
  Octokit: jest.fn().mockImplementation(() => ({
    pulls: { get: mockGet },
  })),
}));

describe('fetchPrDiff', () => {
  const pr = { owner: 'owner', repo: 'repo', pull_number: 1 };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('returns diff string for valid PR', async () => {
    mockGet.mockResolvedValue({ data: 'diff --git a/foo.ts b/foo.ts\n+new line' });
    const diff = await fetchPrDiff(pr, 'fake-token');
    expect(typeof diff).toBe('string');
    expect(diff.length).toBeGreaterThan(0);
  });

  it('truncates diffs larger than 80KB', async () => {
    const largeDiff = 'x'.repeat(100_000);
    mockGet.mockResolvedValue({ data: largeDiff });
    const diff = await fetchPrDiff(pr, 'token');
    expect(diff).toContain('[DIFF TRUNCATED');
    expect(diff.length).toBeLessThan(100_000);
  });

  it('throws on empty diff', async () => {
    mockGet.mockResolvedValue({ data: '   ' });
    await expect(fetchPrDiff(pr, 'token')).rejects.toThrow('PR diff is empty');
  });

  it('throws on API error', async () => {
    mockGet.mockRejectedValue(new Error('Not Found'));
    await expect(fetchPrDiff(pr, 'token')).rejects.toThrow('Failed to fetch PR diff: Not Found');
  });

  it('passes the token to Octokit', async () => {
    mockGet.mockResolvedValue({ data: 'diff content' });
    await fetchPrDiff(pr, 'my-secret-token');
    const { Octokit } = require('@octokit/rest');
    expect(Octokit).toHaveBeenCalledWith({ auth: 'my-secret-token' });
  });
});