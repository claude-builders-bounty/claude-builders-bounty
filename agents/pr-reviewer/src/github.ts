import { Octokit } from '@octokit/rest';
import { PrCoordinates } from './types';

const MAX_DIFF_BYTES = 80_000;

export async function fetchPrDiff(
  pr: PrCoordinates,
  token: string
): Promise<string> {
  const octokit = new Octokit({ auth: token });

  let diff: string;
  try {
    const response = await octokit.pulls.get({
      owner: pr.owner,
      repo: pr.repo,
      pull_number: pr.pull_number,
      mediaType: { format: 'diff' },
    });
    diff = response.data as unknown as string;
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    throw new Error(`Failed to fetch PR diff: ${msg}`);
  }

  if (!diff || (diff as string).trim().length === 0) {
    throw new Error('PR diff is empty — the PR may be closed or have no changes.');
  }

  if (diff.length > MAX_DIFF_BYTES) {
    const truncated = diff.slice(0, MAX_DIFF_BYTES);
    return (
      truncated +
      `\n\n[DIFF TRUNCATED: original size ${diff.length} bytes exceeded ${MAX_DIFF_BYTES} byte limit. ` +
      `Remaining ${diff.length - MAX_DIFF_BYTES} bytes omitted.]`
    );
  }

  return diff;
}