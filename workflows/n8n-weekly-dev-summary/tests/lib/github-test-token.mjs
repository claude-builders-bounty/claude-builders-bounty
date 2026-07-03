/**
 * Resolve GitHub token for CI integration tests and local pre-flight checks.
 * Prefers UPSTREAM_STATUS_TOKEN (dedicated PAT in CI) over GITHUB_TOKEN or gh CLI.
 */
import { execSync } from 'node:child_process';

export function resolveGitHubTestToken() {
  const upstream = (process.env.UPSTREAM_STATUS_TOKEN || '').trim();
  if (upstream) return upstream;

  const fromEnv = (process.env.GITHUB_TOKEN || '').trim();
  if (fromEnv) return fromEnv;

  try {
    return execSync('gh auth token', {
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'ignore'],
    }).trim();
  } catch {
    return '';
  }
}

export function describeGitHubTestTokenSource() {
  if ((process.env.UPSTREAM_STATUS_TOKEN || '').trim()) return 'UPSTREAM_STATUS_TOKEN';
  if ((process.env.GITHUB_TOKEN || '').trim()) return 'GITHUB_TOKEN';
  return 'gh auth token';
}
