'use strict';

const { parsePrUrl, fetchPrData, postComment } = require('./github');
const { buildPrompt, reviewWithClaude, formatReviewComment, validateReview } = require('./reviewer');

async function run(prUrl, options = {}) {
  const { token, post } = options;

  const { owner, repo, number } = parsePrUrl(prUrl);

  const prData = await fetchPrData(owner, repo, number, token);
  prData.number = number;

  const prompt = buildPrompt(prData);
  const review = await reviewWithClaude(prompt);

  const validation = validateReview(review);
  if (!validation.valid) {
    throw new Error(`Review missing required sections: ${validation.missing.join(', ')}`);
  }

  const comment = formatReviewComment(review, prData);

  if (post) {
    await postComment(owner, repo, number, comment, token);
  }

  return comment;
}

module.exports = { run };
