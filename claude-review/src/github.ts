import { Octokit } from "@octokit/rest";

export interface PRInfo {
  owner: string;
  repo: string;
  prNumber: number;
  title: string;
  body: string;
  diff: string;
  files: string[];
  additions: number;
  deletions: number;
  author: string;
  baseBranch: string;
  headBranch: string;
}

export function parsePRUrl(url: string): { owner: string; repo: string; prNumber: number } {
  // Handle both github.com and raw GitHub enterprise URLs
  const patterns = [
    /github\.com\/([^\/]+)\/([^\/]+)\/pull\/(\d+)/,
    /api\.github\.com\/repos\/([^\/]+)\/([^\/]+)\/pulls\/(\d+)/
  ];

  for (const pattern of patterns) {
    const match = url.match(pattern);
    if (match) {
      return {
        owner: match[1],
        repo: match[2],
        prNumber: parseInt(match[3], 10)
      };
    }
  }

  throw new Error(`Invalid PR URL: ${url}`);
}

export async function fetchPRInfo(url: string, token?: string): Promise<PRInfo> {
  const { owner, repo, prNumber } = parsePRUrl(url);
  
  const octokit = new Octokit({
    auth: token || process.env.GITHUB_TOKEN
  });

  // Get PR details
  const { data: pr } = await octokit.rest.pulls.get({
    owner,
    repo,
    pull_number: prNumber
  });

  // Get PR diff
  const diffResponse = await octokit.rest.pulls.get({
    owner,
    repo,
    pull_number: prNumber,
    mediaType: {
      format: "diff"
    }
  });

  const diff = Buffer.isBuffer(diffResponse.data) 
    ? diffResponse.data.toString("utf-8")
    : (diffResponse.data as unknown as string);

  // Get changed files
  const { data: files } = await octokit.rest.pulls.listFiles({
    owner,
    repo,
    pull_number: prNumber
  });

  let totalAdditions = 0;
  let totalDeletions = 0;
  const fileNames = files.map(f => f.filename);
  
  files.forEach(f => {
    totalAdditions += f.additions || 0;
    totalDeletions += f.deletions || 0;
  });

  return {
    owner,
    repo,
    prNumber,
    title: pr.title || "",
    body: pr.body || "",
    diff,
    files: fileNames,
    additions: totalAdditions,
    deletions: totalDeletions,
    author: pr.user?.login || "unknown",
    baseBranch: pr.base?.ref || "main",
    headBranch: pr.head?.ref || "feature"
  };
}

export async function postPRComment(url: string, comment: string, token?: string): Promise<void> {
  const { owner, repo, prNumber } = parsePRUrl(url);
  
  const octokit = new Octokit({
    auth: token || process.env.GITHUB_TOKEN
  });

  await octokit.rest.issues.createComment({
    owner,
    repo,
    issue_number: prNumber,
    body: comment
  });
}
