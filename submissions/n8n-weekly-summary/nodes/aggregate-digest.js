// =========================================================================
// 📊 AGGREGATE GITHUB ACTIVITY DIGEST & SYNTHESIS
// =========================================================================

// Safe synchronization check across incoming branches
let commitsReady = false;
let issuesReady = false;
let prsReady = false;

try { commitsReady = $('GitHub Commits').all().length >= 0; } catch (e) {}
try { issuesReady = $('GitHub Issues').all().length >= 0; } catch (e) {}
try { prsReady = $('GitHub Merged PRs').all().length >= 0; } catch (e) {}

if (!commitsReady || !issuesReady || !prsReady) {
  return [];
}

// Execution deduplication check
const runKey = ($execution && $execution.id) ? $execution.id : ('run_' + Date.now());
const staticData = getWorkflowStaticData('global');
if (staticData[runKey]) {
  return [];
}
staticData[runKey] = true;

const cfg = $('Workflow Configuration').first().json;

// Safely extract items from n8n nodes
const getItems = (nodeName) => {
  try {
    const raw = $(nodeName).all();
    return raw.flatMap(i => {
      if (!i.json) return [];
      if (Array.isArray(i.json)) return i.json;
      if (i.json.message && (i.json.message.includes('API rate limit') || i.json.message.includes('Not Found'))) {
        return [];
      }
      return [i.json];
    }).filter(item => item && typeof item === 'object' && Object.keys(item).length > 0);
  } catch (e) {
    return [];
  }
};

const rawCommits = getItems('GitHub Commits');
const rawIssues = getItems('GitHub Issues');
const rawPRs = getItems('GitHub Merged PRs');

const sinceTime = new Date(cfg.sinceISO).getTime();

// 1. Process Commits
const validCommits = rawCommits.filter(c => c && c.sha && c.commit);
const commitSummaries = validCommits.slice(0, 50).map(c => {
  const firstLine = (c.commit?.message || '').split('\n')[0].trim();
  const author = c.commit?.author?.name || c.author?.login || 'contributor';
  const shortSha = c.sha ? c.sha.substring(0, 7) : '';
  return `- [\`${shortSha}\`] ${firstLine} (by ${author})`;
});

// 2. Process Closed Issues (filtering out PRs which GitHub includes in /issues)
const realClosedIssues = rawIssues.filter(i => {
  if (!i || !i.id || i.pull_request) return false;
  if (i.closed_at) {
    return new Date(i.closed_at).getTime() >= sinceTime;
  }
  return true;
});

const issueSummaries = realClosedIssues.slice(0, 30).map(i => {
  const labels = (i.labels || []).map(l => l.name).filter(Boolean);
  const labelStr = labels.length > 0 ? ` [${labels.slice(0, 2).join(', ')}]` : '';
  return `- #${i.number} "${i.title}"${labelStr} — closed by ${i.user?.login || 'user'}`;
});

// 3. Process Merged Pull Requests (filtering for merged_at within lookback window)
const mergedPRs = rawPRs.filter(p => {
  if (!p || !p.id || !p.merged_at) return false;
  return new Date(p.merged_at).getTime() >= sinceTime;
});

const prSummaries = mergedPRs.slice(0, 30).map(p => {
  const author = p.user?.login || 'contributor';
  return `- PR #${p.number} "${p.title}" — merged by ${author}`;
});

// Statistics
const stats = {
  totalCommits: validCommits.length,
  totalClosedIssues: realClosedIssues.length,
  totalMergedPRs: mergedPRs.length,
  periodStart: cfg.sinceFormatted,
  periodEnd: cfg.untilFormatted
};

// Prepare bilingual prompt for Claude Sonnet 4
const isFrench = cfg.language === 'FR';

const systemPrompt = isFrench
  ? `Tu es un Lead Software Engineer et Technical Writer de premier ordre chargé de générer un résumé narratif hebdomadaire percutant, fluide et professionnel pour le dépôt GitHub "${cfg.repoFullName}". Ton style est soigné, valorise le travail technique accompli, met en avant l'impact des changements et engage les équipes.`
  : `You are an elite Lead Software Engineer and Technical Writer crafting an engaging, narrative executive weekly summary of engineering activity for the GitHub repository "${cfg.repoFullName}". Your tone is clear, insightful, professional, and celebrates the engineering achievements and velocity of the team.`;

const userPrompt = isFrench
  ? `Génère une synthèse narrative hebdomadaire complète en FRANÇAIS pour le dépôt **${cfg.repoFullName}** pour la période du **${cfg.sinceFormatted} au ${cfg.untilFormatted}**.

Données d'activité de la semaine :
- **Commits récents (${stats.totalCommits}) :**
${commitSummaries.length > 0 ? commitSummaries.join('\n') : 'Aucun commit enregistré sur cette période.'}

- **Pull Requests fusionnées (${stats.totalMergedPRs}) :**
${prSummaries.length > 0 ? prSummaries.join('\n') : 'Aucune PR fusionnée sur cette période.'}

- **Issues résolues (${stats.totalClosedIssues}) :**
${issueSummaries.length > 0 ? issueSummaries.join('\n') : 'Aucune issue fermée sur cette période.'}

Structure attendue en Markdown propre :
1. **🌟 Faits Marquants & Vision d'Ensemble** : Résumé narratif en 1-2 paragraphes synthétisant les accomplissements majeurs et le cap du projet cette semaine.
2. **🚀 Nouvelles Fonctionnalités & Améliorations Clés** : Analyse des PRs fusionnées les plus importantes et de leur apport technique.
3. **🛠️ Correctifs & Fiabilisation** : Analyse des bugs résolus et de la consolidation de l'infrastructure.
4. **📊 Dynamique & Vélocité** : Bilan chiffré (${stats.totalCommits} commits, ${stats.totalMergedPRs} PRs fusionnées, ${stats.totalClosedIssues} issues résolues) et remerciements aux contributeurs actifs.
5. **🎯 Perspectives pour la Semaine Prochaine** : Élan impulsé et points de mire techniques.`
  : `Generate a comprehensive, narrative weekly engineering summary in ENGLISH for the repository **${cfg.repoFullName}** covering **${cfg.sinceFormatted} to ${cfg.untilFormatted}**.

Weekly Repository Activity Data:
- **Recent Commits (${stats.totalCommits}):**
${commitSummaries.length > 0 ? commitSummaries.join('\n') : 'No commits recorded during this window.'}

- **Merged Pull Requests (${stats.totalMergedPRs}):**
${prSummaries.length > 0 ? prSummaries.join('\n') : 'No pull requests merged during this window.'}

- **Closed Issues (${stats.totalClosedIssues}):**
${issueSummaries.length > 0 ? issueSummaries.join('\n') : 'No issues closed during this window.'}

Required Markdown Structure:
1. **🌟 Executive Overview & Key Highlights**: 1-2 narrative paragraphs capturing the big-picture achievements, momentum, and technical direction of the repository this week.
2. **🚀 Key Features & Merged Pull Requests**: Narrative breakdown of impactful pull requests and what they contribute to the project.
3. **🛠️ Bug Fixes & Resolved Issues**: Breakdown of key defects resolved, stability enhancements, and closed tickets.
4. **📊 Team Velocity & Contributor Spotlight**: Summary of key metrics (${stats.totalCommits} commits, ${stats.totalMergedPRs} merged PRs, ${stats.totalClosedIssues} closed issues) celebrating team progress.
5. **🎯 Outlook & Focus for Next Week**: Strategic momentum and engineering priorities for the upcoming cycle.`;

return [{
  json: {
    ...cfg,
    stats,
    commitCount: validCommits.length,
    issueCount: realClosedIssues.length,
    prCount: mergedPRs.length,
    systemPrompt,
    userPrompt
  }
}];
