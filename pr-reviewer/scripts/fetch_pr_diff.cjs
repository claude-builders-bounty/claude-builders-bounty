const { execSync } = require('child_process');

function fetchPrDiff(prUrl) {
  if (!prUrl) {
    console.error('Error: PR URL is required.');
    process.exit(1);
  }

  // Ensure it's a valid GitHub PR URL and append .diff
  let diffUrl = prUrl;
  if (!diffUrl.endsWith('.diff')) {
    diffUrl = diffUrl.replace(/\/$/, '') + '.diff';
  }

  const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
  
  try {
    const authHeader = GITHUB_TOKEN ? `-H "Authorization: token ${GITHUB_TOKEN}"` : '';
    const command = `curl -sL ${authHeader} "${diffUrl}"`;
    const diff = execSync(command, { encoding: 'utf-8', maxBuffer: 10 * 1024 * 1024 });
    
    if (!diff || diff.trim().length === 0) {
      console.error('Error: Fetched diff is empty. Check the URL and permissions.');
      process.exit(1);
    }

    console.log(diff);
  } catch (error) {
    console.error(`Error fetching diff: ${error.message}`);
    process.exit(1);
  }
}

const prUrl = process.argv[2];
fetchPrDiff(prUrl);
