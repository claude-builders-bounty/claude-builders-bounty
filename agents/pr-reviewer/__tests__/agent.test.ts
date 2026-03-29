import { runReviewAgent } from '../src/agent';

const mockCreate = jest.fn();

jest.mock('@anthropic-ai/sdk', () => {
  return jest.fn().mockImplementation(() => ({
    messages: { create: mockCreate },
  }));
});

describe('runReviewAgent', () => {
  const SAMPLE_REVIEW = `## Summary
This PR adds a new feature to the codebase that improves user experience. The changes are well-structured and follow existing patterns.

## Risks
- Missing error handling in \`src/utils.ts:42\`

## Improvement Suggestions
- Consider adding unit tests for the new \`formatDate\` function in \`src/utils.ts\`

## Confidence Score
High — The diff is small and focused, making analysis straightforward.`;

  beforeEach(() => {
    jest.clearAllMocks();
    mockCreate.mockResolvedValue({
      content: [{ type: 'text', text: SAMPLE_REVIEW }],
    });
  });

  it('returns structured markdown with all required sections', async () => {
    const output = await runReviewAgent('diff --git a/foo.ts...', 'fake-key');
    expect(output).toContain('## Summary');
    expect(output).toContain('## Risks');
    expect(output).toContain('## Improvement Suggestions');
    expect(output).toContain('## Confidence Score');
  });

  it('includes confidence score of Low, Medium, or High', async () => {
    const output = await runReviewAgent('diff content', 'fake-key');
    expect(output).toMatch(/Confidence Score[\s\S]*(Low|Medium|High)/);
  });

  it('throws on unexpected response type', async () => {
    mockCreate.mockResolvedValue({
      content: [{ type: 'image', source: {} }],
    });
    await expect(runReviewAgent('diff', 'key')).rejects.toThrow(
      'Unexpected response type from Claude API'
    );
  });

  it('calls the Anthropic API with the diff in the message', async () => {
    await runReviewAgent('my diff content', 'test-api-key');
    expect(mockCreate).toHaveBeenCalledWith(
      expect.objectContaining({
        messages: expect.arrayContaining([
          expect.objectContaining({
            content: expect.stringContaining('my diff content'),
          }),
        ]),
      })
    );
  });
});