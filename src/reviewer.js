const { Octokit } = require('@octokit/rest');
const Anthropic = require('@anthropic/claude');

// Initialize Octokit with GitHub token
const octokit = new Octokit({
  auth: process.env.GITHUB_TOKEN
});

// Initialize Claude client
const claude = new Anthropic({
  apiKey: process.env.CLAUDE_API_KEY
});

async function getPRDiff(owner, repo, prNumber) {
  const { data } = await octokit.pulls.get({
    owner,
    repo,
    pull_number: prNumber
  });
  
  const { data: files } = await octokit.pulls.listFiles({
    owner,
    repo,
    pull_number: prNumber
  });
  
  let diffContent = '';
  files.forEach(file => {
    diffContent += `--- a/${file.filename}\n+++ b/${file.filename}\n${file.patch}\n\n`;
  });
  
  return {
    title: data.title,
    description: data.body || '',
    diff: diffContent
  };
}

async function analyzeWithClaude(prData) {
  const prompt = `Analyze this pull request and provide a structured review:

Title: ${prData.title}
Description: ${prData.description}
Diff:
${prData.diff}

Provide your response in this exact format:
## Summary of Changes
[2-3 sentences summarizing the changes]

## Risks
- [List of identified risks]

## Suggestions
- [List of improvement suggestions]

## Confidence
[Low/Medium/High]
`;

  const response = await claude.messages.create({
    model: 'claude-3-opus-20240229',
    max_tokens: 1000,
    messages: [
      {
        role: 'user',
        content: prompt
      }
    ]
  });

  return response.content[0].text;
}

async function reviewPR(prUrl) {
  // Parse GitHub URL
  const urlParts = prUrl.match(/github\.com\/([^\/]+)\/([^\/]+)\/pull\/(\d+)/);
  if (!urlParts) {
    throw new Error('Invalid GitHub PR URL');
  }
  
  const [, owner, repo, prNumber] = urlParts;
  
  // Get PR data
  const prData = await getPRDiff(owner, repo, parseInt(prNumber));
  
  // Analyze with Claude
  const analysis = await analyzeWithClaude(prData);
  
  return analysis;
}

module.exports = { reviewPR };