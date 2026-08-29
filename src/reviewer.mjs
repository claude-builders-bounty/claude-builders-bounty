import { generateClaudeReview, repairClaudeReview } from './claude.mjs';
import { validateReviewMarkdown } from './format.mjs';

export async function reviewInput(prInput, options = {}) {
  let output = await generateClaudeReview(prInput, options);
  let validation = validateReviewMarkdown(output);

  if (!validation.ok && options.repair !== false) {
    output = await repairClaudeReview(prInput, output, validation.errors, options);
    validation = validateReviewMarkdown(output);
  }

  if (!validation.ok) {
    throw new Error(`Claude returned invalid review Markdown: ${validation.errors.join('; ')}`);
  }

  return {
    markdown: validation.markdown,
    confidence: validation.confidence,
  };
}
