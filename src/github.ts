import { Octokit } from "@octokit/rest";

export class GitHubClient {
  private octokit: Octokit;

  constructor(token?: string) {
    this.octokit = new Octokit({
      auth: token || process.env.GITHUB_TOKEN,
    });
  }

  async getIssue(owner: string, repo: string, issueNumber: number): Promise<any> {
    try {
      const { data } = await this.octokit.issues.get({
        owner,
        repo,
        issue_number: issueNumber,
      });
      return data;
    } catch (error) {
      console.error(`Failed to fetch issue #${issueNumber}:`, error);
      throw error;
    }
  }

  async createComment(owner: string, repo: string, issueNumber: number, body: string): Promise<any> {
    try {
      const { data } = await this.octokit.issues.createComment({
        owner,
        repo,
        issue_number: issueNumber,
        body,
      });
      return data;
    } catch (error) {
      console.error(`Failed to create comment on issue #${issueNumber}:`, error);
      throw error;
    }
  }

  async getRepoIssues(owner: string, repo: string, state: "open" | "closed" = "open"): Promise<any[]> {
    try {
      const issues: any[] = [];
      for await (const response of this.octokit.paginate.iterator(
        this.octokit.issues.listForRepo,
        {
          owner,
          repo,
          state,
          per_page: 100,
        }
      )) {
        issues.push(...response.data);
      }
      return issues;
    } catch (error) {
      console.error(`Failed to fetch issues for ${owner}/${repo}:`, error);
      throw error;
    }
  }

  async addLabel(owner: string, repo: string, issueNumber: number, label: string): Promise<void> {
    try {
      await this.octokit.issues.addLabels({
        owner,
        repo,
        issue_number: issueNumber,
        labels: [label],
      });
    } catch (error) {
      console.error(`Failed to add label to issue #${issueNumber}:`, error);
    }
  }

  async removeLabel(owner: string, repo: string, issueNumber: number, label: string): Promise<void> {
    try {
      await this.octokit.issues.removeLabel({
        owner,
        repo,
        issue_number: issueNumber,
        name: label,
      });
    } catch (error) {
      console.error(`Failed to remove label from issue #${issueNumber}:`, error);
    }
  }
}
