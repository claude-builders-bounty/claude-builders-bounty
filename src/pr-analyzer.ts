import { Claude } from '@anthropic-ai/sdk';

const claude = new Claude({
  apiKey: process.env.ANTHROPIC_API_KEY,
});

export interface PRAnalysis {
  summary: string;
  risks: string[];
  suggestions: string[];
  confidence: 'Low' | 'Medium' | 'High';
}

export async function analyzePR(diff: string, prUrl: string): Promise<PRAnalysis> {
  const prompt = `
You are an expert code reviewer. Analyze the following pull request diff and provide a structured review.

PR URL: ${prUrl}

Diff:
${diff}

Please analyze this code and provide:
1. A concise summary of changes (2-3 sentences)
2. Identified risks (list format)
3. Improvement suggestions (list format)
4. Confidence score: Low / Medium / High

Respond in JSON format with the following structure:
{
  "summary": "string",
  "risks": ["string"],
  "suggestions": ["string"],
  "confidence": "Low" | "Medium" | "High"
}
`;

  try {
    const response = await claude.messages.create({
      model: 'claude-3-sonnet-20240229',
      max_tokens: 1000,
      messages: [
        { role: 'user', content: prompt }
      ]
    });

    const content = response.content[0].text;
    
    // Parse JSON response
    const analysis: PRAnalysis = JSON.parse(content);
    
    return analysis;
  } catch (error) {
    console.error('Error analyzing PR with Claude:', error);
    
    // Fallback analysis if Claude API fails
    return {
      summary: 'Unable to analyze PR due to API error',
      risks: ['Analysis failed - please review manually'],
      suggestions: ['Retry with valid API key'],
      confidence: 'Low'
    };
  }
}