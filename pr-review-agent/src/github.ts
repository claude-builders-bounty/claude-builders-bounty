import { Octokit } from 'octokit';

export interface PRInfo {
  owner: string;
  repo: string;
  number: number;
  title: string;
  body: string;
  diff: string;
  files: string[];
}

export interface GitHubConfig {
  token?: string;
}

export function parsePRUrl(url: string): { owner: string; repo: string; number: number } {
  // Handle various GitHub URL formats
  const patterns = [
    /github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)/,
    /github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)\//,
  ];

  for (const pattern of patterns) {
    const match = url.match(pattern);
    if (match) {
      return {
        owner: match[1],
        repo: match[2],
        number: parseInt(match[3], 10),
      };
    }
  }

  throw new Error(`Invalid PR URL: ${url}`);
}

export async function getPRInfo(url: string, config: GitHubConfig): Promise<PRInfo> {
  const { owner, repo, number } = parsePRUrl(url);

  const octokit = new Octokit({
    auth: config.token,
  });

  // Fetch PR details and diff
  const [prResponse, filesResponse] = await Promise.all([
    octokit.rest.pulls.get({ owner, repo, pull_number: number }),
    octokit.rest.pulls.listFiles({ owner, repo, pull_number: number }),
  ]);

  const pr = prResponse.data;

  // Get diff as a string
  const diffResponse = await octokit.rest.pulls.get({
    owner,
    repo,
    pull_number: number,
    headers: { Accept: 'application/vnd.github.v3.diff' },
  });
  const diff = typeof diffResponse.data === 'string' ? diffResponse.data : '';

  const files = filesResponse.data.map((f) => f.filename);

  return {
    owner,
    repo,
    number,
    title: pr.title || '',
    body: pr.body || '',
    diff,
    files,
  };
}
