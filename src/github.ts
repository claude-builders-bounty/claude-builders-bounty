import { Octokit } from "@octokit/rest";

export interface PRInfo {
  owner: string;
  repo: string;
  prNumber: number;
  title: string;
  body: string;
  diff: string;
  filesChanged: string[];
  additions: number;
  deletions: number;
}

export async function fetchPR(prUrl: string, token?: string): Promise<PRInfo> {
  const parsed = parsePRUrl(prUrl);
  if (!parsed) throw new Error(`Invalid PR URL: ${prUrl}`);

  const octokit = new Octokit({ auth: token });

  const [prResp, filesResp] = await Promise.all([
    octokit.rest.pulls.get({ ...parsed }),
    octokit.rest.pulls.listFiles({ ...parsed, per_page: 100 }),
  ]);

  const pr = prResp.data;
  const files = filesResp.data;

  // Get diff
  const diffResp = await octokit.rest.pulls.get({
    ...parsed,
    headers: { Accept: "application/vnd.github.v3.diff" },
  });
  const diff = typeof diffResp.data === "string" ? diffResp.data : "";

  return {
    owner: parsed.owner,
    repo: parsed.repo,
    prNumber: parsed.pull_number,
    title: pr.title,
    body: pr.body ?? "",
    diff,
    filesChanged: files.map((f) => f.filename),
    additions: files.reduce((sum, f) => sum + f.additions, 0),
    deletions: files.reduce((sum, f) => sum + f.deletions, 0),
  };
}

function parsePRUrl(url: string): { owner: string; repo: string; pull_number: number } | null {
  const match = url.match(/github\.com\/([^\/]+)\/([^\/]+)\/pull\/([0-9]+)/);
  if (!match) return null;
  return {
    owner: match[1],
    repo: match[2],
    pull_number: parseInt(match[3], 10),
  };
}