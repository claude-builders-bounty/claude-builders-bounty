import { describe, it, expect, vi } from 'vitest';
import { GitHubService } from '../src/github.js';

describe('GitHubService', () => {
  const service = new GitHubService('dummy-token');

  it('parses PR URL correctly', () => {
    const res = service.parsePRUrl('https://github.com/owner/repo/pull/123');
    expect(res).toEqual({ owner: 'owner', repo: 'repo', number: 123 });
  });

  it('throws on invalid URL', () => {
    expect(() => service.parsePRUrl('https://github.com/owner/repo/issues/123'))
      .toThrow('Invalid GitHub PR URL format');
  });
});
