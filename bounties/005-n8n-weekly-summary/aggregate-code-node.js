// Code - Aggregate Data Node (JavaScript for n8n)
// This code aggregates data from GitHub nodes and builds the prompt for Claude

// Get inputs from previous nodes
const commits = $input.all()[0]?.json || [];
const issues = $input.all()[1]?.json || [];
const prs = $input.all()[2]?.json || [];

// Get config from Set Config node
const config = $items('Set Config')[0].json;
const { githubOwner, githubRepo, language, weekStart, weekEnd } = config;

// Calculate week label
const weekLabel = `${new Date(weekStart).toLocaleDateString()} - ${new Date(weekEnd).toLocaleDateString()}`;

// Filter data for the current week (GitHub API may return extra)
const weekStartDate = new Date(weekStart);
const weekEndDate = new Date(weekEnd);

const filterByDate = (items, dateField) => {
  return items.filter(item => {
    const date = new Date(item[dateField] || item.created_at);
    return date >= weekStartDate && date <= weekEndDate;
  });
};

const weeklyCommits = filterByDate(commits, 'commit.author.date');
const weeklyIssues = filterByDate(issues, 'closed_at');
const weeklyPRs = filterByDate(prs, 'merged_at');

// Extract contributor stats
const contributorStats = {};
weeklyCommits.forEach(commit => {
  const author = commit.commit?.author?.name || commit.author?.login || 'Unknown';
  contributorStats[author] = (contributorStats[author] || 0) + 1;
});

const topContributors = Object.entries(contributorStats)
  .sort((a, b) => b[1] - a[1])
  .slice(0, 5);

// Build the prompt for Claude
const languageInstruction = language === 'FR' 
  ? 'Écris le résumé en français.' 
  : 'Write the summary in English.';

const prompt = `Generate a weekly development summary for the repository ${githubOwner}/${githubRepo}.

WEEK: ${weekLabel}

ACTIVITY DATA:
- Commits: ${weeklyCommits.length}
- Closed Issues: ${weeklyIssues.length}
- Merged Pull Requests: ${weeklyPRs.length}

TOP CONTRIBUTORS:
${topContributors.map(([name, count]) => `- ${name}: ${count} commits`).join('\n')}

CLOSED ISSUES:
${weeklyIssues.slice(0, 10).map(i => `- #${i.number}: ${i.title}`).join('\n')}

MERGED PULL REQUESTS:
${weeklyPRs.slice(0, 10).map(p => `- #${p.number}: ${p.title} by @${p.user?.login}`).join('\n')}

RECENT COMMITS:
${weeklyCommits.slice(0, 10).map(c => `- ${c.commit?.message?.split('\n')[0]} (${c.commit?.author?.name})`).join('\n')}

INSTRUCTIONS:
Write a friendly, professional weekly summary suitable for a team standup or newsletter.
Include:
1. A brief opening with total stats
2. Key highlights (major PRs, important fixes)
3. Contributor recognition
4. A closing with next week anticipation

Keep it concise (200-300 words) and engaging.
${languageInstruction}`;

// Return aggregated data for Claude
return [{
  json: {
    prompt: prompt,
    stats: {
      commits: weeklyCommits.length,
      issues: weeklyIssues.length,
      prs: weeklyPRs.length,
      contributors: topContributors
    },
    weekLabel: weekLabel,
    config: config
  }
}];
