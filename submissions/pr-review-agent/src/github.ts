import { Octokit } from '@octokit/rest';
import { PRInfo, PRDiff } from './types.js';

export class GitHubService {
  private octokit: Octokit;

  constructor(token: string) {
    this.octokit = new Octokit({ auth: token });
  }

  /**
   * Parse a GitHub PR URL into owner, repo, and PR number
   */
  parsePRUrl(url: string): { owner: string; repo: string; number: number } {
    const match = url.match(/github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)/);
    if (!match) {
      throw new Error(`Invalid GitHub PR URL format: ${url}`);
    }
    return {
      owner: match[1],
      repo: match[2],
      number: parseInt(match[3], 10),
    };
  }

  /**
   * Fetch PR details
   */
  async getPRInfo(owner: string, repo: string, number: number): Promise<PRInfo> {
    const { data: pr } = await this.octokit.pulls.get({
      owner,
      repo,
      pull_number: number,
    });

    return {
      owner,
      repo,
      number,
      title: pr.title,
      description: pr.body || '',
      author: pr.user?.login || 'unknown',
      baseBranch: pr.base.ref,
      headBranch: pr.head.ref,
      labels: pr.labels.map(l => l.name),
    };
  }

  /**
   * Fetch PR diff and files changed
   */
  async getPRDiff(owner: string, repo: string, number: number): Promise<PRDiff> {
    const { data: files } = await this.octokit.pulls.listFiles({
      owner,
      repo,
      pull_number: number,
      per_page: 100,
    });

    const { data: diff } = await this.octokit.pulls.get({
      owner,
      repo,
      pull_number: number,
      mediaType: {
        format: 'diff',
      },
    });

    const additions = files.reduce((sum, file) => sum + file.additions, 0);
    const deletions = files.reduce((sum, file) => sum + file.deletions, 0);

    // Truncate diff if it's too large (over 100,000 characters)
    let rawDiff = diff as unknown as string;
    if (rawDiff.length > 100000) {
      rawDiff = rawDiff.substring(0, 100000) + '\n\n...[DIFF TRUNCATED DUE TO SIZE]...';
    }

    return {
      files: files.length,
      additions,
      deletions,
      rawDiff,
    };
  }

  /**
   * Post a comment on a PR
   */
  async postComment(owner: string, repo: string, number: number, body: string): Promise<void> {
    await this.octokit.issues.createComment({
      owner,
      repo,
      issue_number: number,
      body,
    });
  }
}
