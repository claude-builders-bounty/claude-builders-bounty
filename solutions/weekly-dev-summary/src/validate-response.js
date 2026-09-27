if ($json.statusCode !== 200) throw new Error('Claude API request did not succeed');
const response = $json.body;
if (response?.type === 'error') throw new Error('Claude API returned an error response');
if (response?.type !== 'message' || response.role !== 'assistant' || !Array.isArray(response.content)) {
  throw new Error('Claude API returned an invalid message');
}
if (response.stop_reason !== 'end_turn') {
  throw new Error('Claude API did not complete the summary; review its stop reason before retrying');
}
const blocks = response.content.filter((block) => block?.type === 'text');
if (blocks.some((block) => typeof block.text !== 'string')) {
  throw new Error('Claude API returned an invalid text block');
}
const summary = blocks.map((block) => block.text.trim()).filter(Boolean).join('\n\n');
if (!summary) throw new Error('Claude API returned an empty summary');
if (summary.length > 1800) throw new Error('Claude API summary exceeds the delivery limit');

return [{ json: { summary } }];
