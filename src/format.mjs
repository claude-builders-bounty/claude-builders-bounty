const REQUIRED_SECTIONS = [
  '## Summary',
  '## Identified Risks',
  '## Improvement Suggestions',
];

export function normalizeMarkdown(value) {
  let text = String(value ?? '').trim();
  const fenced = text.match(/^```(?:markdown|md)?\s*\n([\s\S]*?)\n```$/i);
  if (fenced) text = fenced[1].trim();
  return text;
}

export function validateReviewMarkdown(value) {
  const markdown = normalizeMarkdown(value);
  const errors = [];

  for (const heading of REQUIRED_SECTIONS) {
    if (!markdown.includes(heading)) errors.push(`missing heading: ${heading}`);
  }

  const confidence = markdown.match(/^## Confidence:\s*(Low|Medium|High)\s*$/im)?.[1] ?? null;
  if (!confidence) errors.push('missing valid confidence heading: ## Confidence: Low|Medium|High');

  const summaryMatch = markdown.match(/^## Summary\s*\n([\s\S]*?)(?=^## Identified Risks\s*$)/im);
  if (!summaryMatch || !summaryMatch[1].trim()) errors.push('summary is empty');

  const risksMatch = markdown.match(/^## Identified Risks\s*\n([\s\S]*?)(?=^## Improvement Suggestions\s*$)/im);
  if (!risksMatch || !/^\s*-\s+\S/m.test(risksMatch[1])) errors.push('risks section must contain at least one bullet');

  const suggestionsMatch = markdown.match(/^## Improvement Suggestions\s*\n([\s\S]*?)(?=^## Confidence:)/im);
  if (!suggestionsMatch || !/^\s*-\s+\S/m.test(suggestionsMatch[1])) errors.push('suggestions section must contain at least one bullet');

  return { ok: errors.length === 0, errors, markdown, confidence };
}
