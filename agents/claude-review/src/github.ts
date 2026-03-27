import fetch from 'node-fetch';

export interface PRInfo {
  owner: string;
  repo: string;
  number: number;
  title: string;
  body: string;
  author: string;
  baseBranch: string;
  headBranch: string;
  files: PRFile[];
}

export interface PRFile {
  filename: string;
  status: string;
  additions: number;
  deletions: number;
  changes: number;
  patch?: string;
}

export class GitHubClient {
  private token: string;
  private baseUrl = 'https://api.github.com';

  constructor(token: string) {
    this.token = token;
  }

  private async fetch(path: string, accept: string = 'application/vnd.github.v3+json'): Promise<any> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Accept': accept,
        'User-Agent': 'claude-review/1.0.0'
      }
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`GitHub API error: ${response.status} ${error}`);
    }

    return response.json();
  }

  async fetchText(path: string): Promise<string> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Accept': 'application/vnd.github.v3.diff',
        'User-Agent': 'claude-review/1.0.0'
      }
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`GitHub API error: ${response.status} ${error}`);
    }

    return response.text();
  }

  parsePRUrl(url: string): { owner: string; repo: string; number: number } {
    // Handle various GitHub PR URL formats
    const patterns = [
      /github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)/,
      /github\.com\/([^/]+)\/([^/]+)\/pulls\/(\d+)/,
    ];

    for (const pattern of patterns) {
      const match = url.match(pattern);
      if (match) {
        return {
          owner: match[1],
          repo: match[2],
          number: parseInt(match[3], 10)
        };
      }
    }

    throw new Error(`Invalid PR URL format: ${url}`);
  }

  async getPRInfo(owner: string, repo: string, prNumber: number): Promise<PRInfo> {
    const pr = await this.fetch(`/repos/${owner}/${repo}/pulls/${prNumber}`);
    const files = await this.fetch(`/repos/${owner}/${repo}/pulls/${prNumber}/files`);

    return {
      owner,
      repo,
      number: prNumber,
      title: pr.title || '',
      body: pr.body || '',
      author: pr.user?.login || 'unknown',
      baseBranch: pr.base?.ref || 'main',
      headBranch: pr.head?.ref || 'unknown',
      files: files.map((f: any) => ({
        filename: f.filename,
        status: f.status,
        additions: f.additions,
        deletions: f.deletions,
        changes: f.changes,
        patch: f.patch
      }))
    };
  }

  async getPRDiff(owner: string, repo: string, prNumber: number): Promise<string> {
    return this.fetchText(`/repos/${owner}/${repo}/pulls/${prNumber}`);
  }

  async getFileContent(owner: string, repo: string, path: string, ref: string): Promise<string | null> {
    try {
      const response = await fetch(`${this.baseUrl}/repos/${owner}/${repo}/contents/${path}?ref=${ref}`, {
        headers: {
          'Authorization': `Bearer ${this.token}`,
          'Accept': 'application/vnd.github.v3.raw',
          'User-Agent': 'claude-review/1.0.0'
        }
      });

      if (!response.ok) {
        return null;
      }

      return response.text();
    } catch {
      return null;
    }
  }
}
