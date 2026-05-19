import { Octokit } from 'octokit';
import { PRInfo, DiffFile } from './types';

export class GitHubClient {
  private octokit: Octokit;

  constructor(token?: string) {
    const auth = token || process.env.GITHUB_TOKEN;
    if (!auth) {
      throw new Error('GitHub token required. Set GITHUB_TOKEN environment variable.');
    }
    this.octokit = new Octokit({ auth });
  }

  parsePRUrl(url: string): PRInfo {
    const match = url.match(/github\.com\/([^\/]+)\/([^\/]+)\/pull\/(\d+)/);
    if (!match) {
      throw new Error(`Invalid PR URL: ${url}`);
    }
    return {
      owner: match[1],
      repo: match[2],
      pullNumber: parseInt(match[3], 10),
      title: '',
      description: ''
    };
  }

  async getPRInfo(owner: string, repo: string, pullNumber: number): Promise<PRInfo> {
    const { data } = await this.octokit.rest.pulls.get({
      owner,
      repo,
      pull_number: pullNumber
    });
    return {
      owner,
      repo,
      pullNumber,
      title: data.title,
      description: data.body || ''
    };
  }

  async getPRDiff(owner: string, repo: string, pullNumber: number): Promise<DiffFile[]> {
    const { data } = await this.octokit.rest.pulls.listFiles({
      owner,
      repo,
      pull_number: pullNumber
    });
    
    return data.map(file => ({
      filename: file.filename,
      status: file.status as DiffFile['status'],
      additions: file.additions,
      deletions: file.deletions,
      patch: file.patch || ''
    }));
  }

  async postComment(owner: string, repo: string, pullNumber: number, body: string): Promise<void> {
    await this.octokit.rest.issues.createComment({
      owner,
      repo,
      issue_number: pullNumber,
      body
    });
  }
}
