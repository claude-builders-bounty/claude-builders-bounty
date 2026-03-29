import { PrCoordinates } from './types';

const PR_URL_REGEX = /^https:\/\/github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)\/?$/;

export function parsePrUrl(url: string): PrCoordinates {
  const match = url.trim().match(PR_URL_REGEX);
  if (!match) {
    throw new Error(
      `Invalid GitHub PR URL: "${url}". Expected format: https://github.com/owner/repo/pull/NUMBER`
    );
  }
  return {
    owner: match[1],
    repo: match[2],
    pull_number: parseInt(match[3], 10),
  };
}