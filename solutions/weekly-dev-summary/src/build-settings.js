const repo = String($json.repo || 'owner/repository').trim();
if (!/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(repo)) {
  throw new Error('repo must use owner/repository format');
}

const now = new Date();
const until = now.toISOString();
const since = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString();

return [{
  json: {
    repo,
    since,
    until,
    language: $json.language === 'fr' ? 'fr' : 'en',
    destinationType: ['discord', 'slack', 'local-test'].includes($json.destinationType)
      ? $json.destinationType
      : 'discord',
    webhookUrl: String($json.webhookUrl || ''),
    sendDelivery: $json.sendDelivery === true,
  },
}];
