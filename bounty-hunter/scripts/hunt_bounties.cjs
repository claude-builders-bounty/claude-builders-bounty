const { execSync } = require('child_process');

async function huntBounties() {
  const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
  const DISCORD_WEBHOOK_URL = process.env.DISCORD_WEBHOOK_URL;
  const MIN_VALUE = 50;
  const MAX_COMMENTS = 10; // "Low Competition"

  console.log('Searching for high-value, low-competition bounties...');

  try {
    const query = encodeURIComponent('label:bounty is:open state:open');
    const authHeader = GITHUB_TOKEN ? `-H "Authorization: token ${GITHUB_TOKEN}"` : '';
    const command = `curl -s ${authHeader} "https://api.github.com/search/issues?q=${query}&sort=created&order=desc"`;
    const response = JSON.parse(execSync(command, { encoding: 'utf-8' }));

    const highValueBounties = response.items.filter(issue => {
      // Extract dollar amount from title or body (e.g. "$100" or "100$")
      const amountMatch = (issue.title + issue.body).match(/\$(\d+)|(\d+)\$/);
      const amount = amountMatch ? parseInt(amountMatch[1] || amountMatch[2]) : 0;
      
      // Filter by value and competition
      return amount >= MIN_VALUE && issue.comments <= MAX_COMMENTS;
    });

    if (highValueBounties.length === 0) {
      console.log('No new high-value bounties found.');
      return;
    }

    console.log(`Found ${highValueBounties.length} opportunities!`);

    for (const bounty of highValueBounties) {
      const message = {
        content: `🎯 **New Bounty Opportunity Found!**\n\n**Title**: ${bounty.title}\n**URL**: ${bounty.html_url}\n**Comments**: ${bounty.comments}\n**Target Reward**: > $${MIN_VALUE}\n\n*Execute immediately for maximum ROI.*`
      };

      console.log(`Processing: ${bounty.title}`);

      if (DISCORD_WEBHOOK_URL) {
        execSync(`curl -s -X POST -H "Content-Type: application/json" -d '${JSON.stringify(message)}' ${DISCORD_WEBHOOK_URL}`);
      } else {
        console.log('DRY RUN: DISCORD_WEBHOOK_URL not set.');
        console.log('Payload:', JSON.stringify(message, null, 2));
      }
    }

  } catch (error) {
    console.error('Error hunting bounties:', error.message);
  }
}

huntBounties();
