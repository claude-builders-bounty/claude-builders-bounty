export function formatChangelogEntry(tag: string, commits: Array<{ hash: string; message: string }>): string {
  return `## ${tag}\n` + commits.map(c => `- ${c.message} (${c.hash.slice(0, 7)})`).join('\n');
}
