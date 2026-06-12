import { request } from "node:https";

/**
 * Minimal GitHub REST client using node:https. Pulled in here instead of
 * pulling in @octokit/rest to keep the dependency surface small.
 */

const GITHUB_API = "api.github.com";

export interface PullRequest {
  title: string;
  author: string;
  baseRef: string;
  headRef: string;
  body: string;
  diff: string;
  url: string;
}

function parsePrUrl(url: string): { owner: string; repo: string; pullNumber: number } | null {
  // Accepts both https://github.com/owner/repo/pull/123 and the
  // patch URL https://github.com/owner/repo/pull/123.patch
  const m = url.match(/github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)/);
  if (!m) return null;
  return { owner: m[1], repo: m[2], pullNumber: Number(m[3]) };
}

function githubGet<T>(path: string, accept: string): Promise<T> {
  const headers: Record<string, string> = {
    "User-Agent": "claude-review/0.1",
    Accept: accept,
  };
  if (process.env.GITHUB_TOKEN) {
    headers["Authorization"] = `Bearer ${process.env.GITHUB_TOKEN}`;
  }
  return new Promise((resolve, reject) => {
    const req = request(
      {
        host: GITHUB_API,
        path,
        method: "GET",
        headers,
      },
      (res) => {
        if (!res.statusCode) {
          reject(new Error("no status code from GitHub"));
          return;
        }
        const chunks: Buffer[] = [];
        res.on("data", (c) => chunks.push(c));
        res.on("end", () => {
          const body = Buffer.concat(chunks).toString("utf8");
          if (res.statusCode! < 200 || res.statusCode! >= 300) {
            reject(new Error(`GitHub API ${res.statusCode}: ${body.slice(0, 200)}`));
            return;
          }
          if (accept.includes("json")) {
            try {
              resolve(JSON.parse(body) as T);
            } catch (e) {
              reject(new Error(`failed to parse GitHub JSON: ${(e as Error).message}`));
            }
          } else {
            resolve(body as unknown as T);
          }
        });
        res.on("error", reject);
      },
    );
    req.on("error", reject);
    req.end();
  });
}

export async function fetchPullRequest(prUrl: string): Promise<PullRequest> {
  const parsed = parsePrUrl(prUrl);
  if (!parsed) {
    throw new Error(
      `could not parse PR URL (expected https://github.com/owner/repo/pull/N): ${prUrl}`,
    );
  }
  const { owner, repo, pullNumber } = parsed;

  // Two requests in parallel: the PR metadata (JSON) and the .patch file (text).
  const [meta, diff] = await Promise.all([
    githubGet<{
      title: string;
      body: string | null;
      user: { login: string } | null;
      base: { ref: string };
      head: { ref: string };
      html_url: string;
    }>(
      `/repos/${owner}/${repo}/pulls/${pullNumber}`,
      "application/vnd.github+json",
    ),
    githubGet<string>(
      `/repos/${owner}/${repo}/pulls/${pullNumber}`,
      "application/vnd.github.v3.patch",
    ),
  ]);

  return {
    title: meta.title,
    author: meta.user?.login ?? "(unknown)",
    baseRef: meta.base.ref,
    headRef: meta.head.ref,
    body: meta.body ?? "",
    diff: diff as unknown as string, // raw text body
    url: meta.html_url,
  };
}
