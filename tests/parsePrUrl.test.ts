/**
 * 测试 PR URL 解析器。
 * 毕竟如果连 URL 都拆不对，后面就不用玩了。
 */
import { describe, it, expect } from 'vitest';

// Inline the parser so we don't need to build first
function parsePrUrl(url: string): { owner: string; repo: string; prNumber: number } {
  const trimmed = url.replace(/\/files$/, '').replace(/\/$/, '');
  const match = trimmed.match(/github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)/);
  if (!match) {
    throw new Error(`无法解析 PR URL: ${url}`);
  }
  return { owner: match[1], repo: match[2], prNumber: parseInt(match[3], 10) };
}

describe('parsePrUrl', () => {
  it('parses a standard PR URL', () => {
    const result = parsePrUrl('https://github.com/owner/repo/pull/123');
    expect(result).toEqual({ owner: 'owner', repo: 'repo', prNumber: 123 });
  });

  it('parses a URL with /files suffix', () => {
    const result = parsePrUrl('https://github.com/foo/bar/pull/456/files');
    expect(result).toEqual({ owner: 'foo', repo: 'bar', prNumber: 456 });
  });

  it('parses a URL with trailing slash', () => {
    const result = parsePrUrl('https://github.com/a/b/pull/789/');
    expect(result).toEqual({ owner: 'a', repo: 'b', prNumber: 789 });
  });

  it('throws on invalid URL', () => {
    expect(() => parsePrUrl('not-a-url')).toThrow('无法解析 PR URL');
  });

  it('throws on non-PR GitHub URL', () => {
    expect(() => parsePrUrl('https://github.com/owner/repo/issues/1')).toThrow('无法解析 PR URL');
  });
});
