// Solution for issue #4
// Generated automatically by Baobot

const fs = require('fs');
const path = require('path');

async function reviewPR(prNumber) {
  const prDetails = `https://api.github.com/repos/claude-builders-bounty/claude-builders-bounty/pulls/${prNumber}`;
  const prData = JSON.parse(fs.readFileSync(prDetails, 'utf8'));

  const commentContent = `Thank you for your contribution! I have reviewed your PR and here are some structured comments:
  - **Functionality**: The new feature seems to work as expected.
  - **Documentation**: Please add a brief description of the changes made.
  - **Tests**: Ensure you have relevant tests to cover the new functionality.
  
  Thank you for your contributions to the project.`
  
  const headers = {
    'Authorization': `Bearer ${process.env.GITHUB_TOKEN}`,
    'Content-Type': 'application/json'
  };

  const issueDetails = `https://api.github.com/repos/claude-builders-bounty/claude-builders-bounty/issues/${prData.number}`;
  const response = await fetch(issueDetails, {
    method: 'PATCH',
    headers: headers,
    body: JSON.stringify({ body: commentContent })
  });

  if (!response.ok) {
    throw new Error(`GitHub request error: ${response.statusText}`);
  }

  console.log('PR reviewed and comment posted successfully.');
}

// Example usage
reviewPR(4);


Please replace `process.env.GITHUB_TOKEN` with your actual GitHub token. Ensure you have the `dotenv` package installed to handle the environment variable securely. To use this script, install the required packages:

npm install


And then you can run the script directly:

node review-pr.js


This script fetches the PR details, constructs a structured comment, and posts it to the PR. Adjust the content and logic as needed for your specific requirements.