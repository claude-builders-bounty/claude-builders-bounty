async function postIssueComment(pr, body, { token }) {
  const url = `https://api.github.com/repos/${pr.owner}/${pr.repo}/issues/${pr.number}/comments`;
  const response = await fetch(url, {
    method: "POST",
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      "User-Agent": "claude-pr-review-agent",
      "X-GitHub-Api-Version": "2022-11-28",
    },
    body: JSON.stringify({ body }),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Failed to post PR comment (${response.status}): ${text}`);
  }
}

module.exports = {
  postIssueComment,
};
