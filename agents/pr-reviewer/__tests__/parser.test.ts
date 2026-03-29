import { parsePrUrl } from '../src/parser';

describe('parsePrUrl', () => {
  it('parses a standard GitHub PR URL', () => {
    const result = parsePrUrl('https://github.com/owner/repo/pull/123');
    expect(result).toEqual({ owner: 'owner', repo: 'repo', pull_number: 123 });
  });

  it('parses URLs with trailing slashes', () => {
    const result = parsePrUrl('https://github.com/owner/repo/pull/123/');
    expect(result).toEqual({ owner: 'owner', repo: 'repo', pull_number: 123 });
  });

  it('parses URLs with numeric owner/repo names', () => {
    const result = parsePrUrl('https://github.com/org123/my-repo/pull/456');
    expect(result).toEqual({ owner: 'org123', repo: 'my-repo', pull_number: 456 });
  });

  it('throws on invalid URLs missing pull segment', () => {
    expect(() => parsePrUrl('https://github.com/owner/repo')).toThrow('Invalid GitHub PR URL');
  });

  it('throws on non-GitHub URLs', () => {
    expect(() => parsePrUrl('https://gitlab.com/owner/repo/pull/1')).toThrow('Invalid GitHub PR URL');
  });

  it('throws on empty string', () => {
    expect(() => parsePrUrl('')).toThrow('Invalid GitHub PR URL');
  });
});