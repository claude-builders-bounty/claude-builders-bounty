import Anthropic from '@anthropic-ai/sdk';
import { PRInfo } from './github';

export interface ReviewResult {
  summary: string;
  risks: string[];
  suggestions: string[];
  confidence: 'Low' | 'Medium' | 'High';
  rawResponse: string;
}

export class ClaudeReviewer {
  private client: Anthropic;

  constructor(apiKey: string) {
    this.client = new Anthropic({ apiKey });
  }

  async reviewPR(prInfo: PRInfo, diff: string): Promise<ReviewResult> {
    const prompt = this.buildPrompt(prInfo, diff);

    const message = await this.client.messages.create({
      model: 'claude-sonnet-4-20250514',
      max_tokens: 4096,
      messages: [{
        role: 'user',
        content: prompt
      }]
    });

    const responseText = message.content[0].type === 'text' 
      ? message.content[0].text 
      : '';

    return this.parseResponse(responseText);
  }

  private buildPrompt(prInfo: PRInfo, diff: string): string {
    const filesSummary = prInfo.files.map(f => 
      `- ${f.filename}: +${f.additions}/-${f.deletions} (${f.status})`
    ).join('\n');

    return `You are an expert code reviewer. Analyze this GitHub Pull Request and provide a structured review.

## PR Information
- **Repository**: ${prInfo.owner}/${prInfo.repo}
- **PR #${prInfo.number}**: ${prInfo.title}
- **Author**: ${prInfo.author}
- **Branch**: ${prInfo.headBranch} → ${prInfo.baseBranch}
- **Description**: ${prInfo.body || '(No description provided)'}

## Files Changed
${filesSummary}

## Full Diff
\`\`\`diff
${diff}
\`\`\`

## Your Task
Provide a thorough code review in the following EXACT format:

### Summary
[2-3 sentences summarizing what this PR does and why]

### Risks
[List each identified risk as a bullet point. Include security concerns, potential bugs, breaking changes, performance issues, etc. Use "None identified" if applicable]

### Suggestions
[List improvement suggestions as bullet points. Include code quality, maintainability, testing, documentation, etc. Use "None at this time" if applicable]

### Confidence
[One of: Low / Medium / High]

---

Your review should be:
1. Specific and actionable
2. Focused on the actual changes in the diff
3. Practical (not overly theoretical)
4. Consider both immediate impact and long-term maintainability

Analyze the code changes now.`;
  }

  private parseResponse(response: string): ReviewResult {
    // Extract sections using regex patterns
    const summaryMatch = response.match(/### Summary\s*\n([\s\S]*?)(?=\n### |$)/i);
    const risksMatch = response.match(/### Risks\s*\n([\s\S]*?)(?=\n### |$)/i);
    const suggestionsMatch = response.match(/### Suggestions\s*\n([\s\S]*?)(?=\n### |$)/i);
    const confidenceMatch = response.match(/### Confidence\s*\n([\s\S]*?)(?=\n### |$)/i);

    const summary = summaryMatch ? summaryMatch[1].trim() : 'Unable to parse summary from response.';
    
    const risks = risksMatch 
      ? this.parseBulletPoints(risksMatch[1])
      : ['Unable to parse risks from response.'];

    const suggestions = suggestionsMatch
      ? this.parseBulletPoints(suggestionsMatch[1])
      : ['Unable to parse suggestions from response.'];

    let confidence: 'Low' | 'Medium' | 'High' = 'Medium';
    if (confidenceMatch) {
      const confText = confidenceMatch[1].trim().toLowerCase();
      if (confText.includes('low')) confidence = 'Low';
      else if (confText.includes('high')) confidence = 'High';
      else if (confText.includes('medium')) confidence = 'Medium';
    }

    return {
      summary,
      risks,
      suggestions,
      confidence,
      rawResponse: response
    };
  }

  private parseBulletPoints(text: string): string[] {
    const lines = text.split('\n')
      .map(line => line.trim())
      .filter(line => line.length > 0);

    const bullets: string[] = [];
    
    for (const line of lines) {
      // Handle various bullet point formats
      const cleaned = line
        .replace(/^[-•*]\s*/, '')
        .replace(/^\d+\.\s*/, '')
        .trim();
      
      if (cleaned && !cleaned.startsWith('###')) {
        bullets.push(cleaned);
      }
    }

    return bullets.length > 0 ? bullets : ['None identified'];
  }
}
