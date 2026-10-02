import { Octokit } from '@octokit/rest';

const octokit = new Octokit({
  auth: process.env.GITHUB_TOKEN,
});

export async function fetchPRDiff(owner: string, repo: string, prNumber: number): Promise<string> {
  const { data: files } = await octokit.rest.pulls.listFiles({
    owner,
    repo,
    pull_number: prNumber,
  });

  const diff = files.map(file => {
    return `File: ${file.filename}\n${file.patch}\n`;
  }).join('\n');

  return diff;
}

export async function getPRInfo(owner: string, repo: string, prNumber: number) {
  const { data: pr } = await octokit.rest.pulls.get({
    owner,
    repo,
    pull_number: prNumber,
  });

  return {
    title: pr.title,
    body: pr.body,
    author: pr.user?.login,
    createdAt: pr.created_at,
    merged: pr.merged,
    labels: pr.labels?.map((label: any) => label.name) || [],
  };
}