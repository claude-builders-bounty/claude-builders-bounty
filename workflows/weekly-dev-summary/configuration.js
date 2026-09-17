const repo = 'octocat/Hello-World'; // Change to owner/repository.
const language = 'EN'; // EN or FR.
const model = 'claude-sonnet-4-6'; // Original bounty model is retired; see MODEL-NOTE.md.
const discordWebhook = 'https://discord.com/api/webhooks/REPLACE/REPLACE';
const until = new Date();
const since = new Date(until.getTime() - 7 * 86400000);
if (!/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(repo)) throw new Error('Invalid owner/repository');
if (!['EN','FR'].includes(language)) throw new Error('Language must be EN or FR');
return [{json:{repo,language,model,discordWebhook,since:since.toISOString(),until:until.toISOString()}}];
